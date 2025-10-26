"""
Full agentic pipeline (LLM modularized via models.py and scoring.py)
"""

import asyncio, os, csv, re, glob
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from tavily import TavilyClient
from bcbs_scraper import get_bcbs_providers_live
from models import get_nemotron
from scoring import compute_final_scores  # ✅ imported scoring logic

# -----------------------------
# Setup
# -----------------------------
load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
llm = get_nemotron()

# -----------------------------
# Graph State
# -----------------------------
class GraphState(TypedDict):
    insurance: Optional[str]
    specialty: Optional[str]
    location: Optional[str]
    postal_code: Optional[str]
    symptom: Optional[str]
    member_id: Optional[str]
    providers: Optional[list]


# -----------------------------
# Step 0: LLM helpers
# -----------------------------
def get_specialty_from_symptom(symptom_description: str) -> str:
    """Infer the most appropriate medical specialty from a symptom/disease."""
    prompt = f"""
You are a medical triage assistant.
Given this patient complaint or disease:
"{symptom_description}"

Return the most relevant specialty in strict JSON:
{{"recommended": "Dermatology"}}
"""
    try:
        resp = llm.invoke(prompt)
        text = resp.content.strip() if hasattr(resp, "content") else str(resp)
        match = re.search(r'"recommended"\s*:\s*"([^"]+)"', text)
        if match:
            specialty = match.group(1).strip()
            print(f"🧠 Inferred specialty: {specialty}")
            return specialty
    except Exception as e:
        print(f"⚠️ Specialty inference failed: {e}")
    return "Internal Medicine"


def is_specialty_term(user_input: str) -> bool:
    """Determine if input is a medical specialty using LLM classification."""
    prompt = f'Is "{user_input}" a valid medical specialty? Answer only YES or NO.'
    try:
        resp = llm.invoke(prompt)
        text = resp.content.strip().upper() if hasattr(resp, "content") else str(resp).upper()
        return text.startswith("YES")
    except Exception as e:
        print(f"⚠️ LLM specialty check failed: {e}")
        return False


# -----------------------------
# Step 1: Collect user info
# -----------------------------
async def get_user_info(state: GraphState):
    print("🧾 Collecting user info...\n")

    user_input = input("🩺 Describe your main symptom or enter a specialty: ").strip()
    state["symptom"] = user_input

    if is_specialty_term(user_input):
        state["specialty"] = user_input
    else:
        state["specialty"] = get_specialty_from_symptom(user_input)

    insurance = input("🏥 Enter your insurance provider (e.g., Blue Cross Blue Shield, Aetna, Cigna): ").strip()
    state["insurance"] = insurance

    if "bcbs" in insurance.lower() or "blue" in insurance.lower():
        member_id = input("💳 Enter your BCBS Member ID or prefix (e.g., ZGP1234567): ").strip()
        prefix = member_id[:3].upper() if len(member_id) >= 3 else "UNK"
        state["member_id"] = prefix
    else:
        state["member_id"] = None

    location = input("📍 Enter your location (City, State ZIP): ").strip()
    postal_match = re.search(r"\b\d{5}\b", location)
    postal_code = postal_match.group(0) if postal_match else input("📬 Enter your ZIP code: ").strip()

    state["location"] = location
    state["postal_code"] = postal_code

    print(f"\n✅ Summary of user input:")
    print(f" - Specialty: {state['specialty']}")
    print(f" - Insurance: {state['insurance']}")
    print(f" - Member ID Prefix: {state.get('member_id', 'N/A')}")
    print(f" - Location: {state['location']}")
    print(f" - Postal Code: {state['postal_code']}\n{'-'*60}")
    return state


# -----------------------------
# Step 2: Provider lookup
# -----------------------------
async def find_providers(state: GraphState):
    insurance = state.get("insurance", "").lower()
    specialty = state.get("specialty")
    location = state.get("location")
    postal = state.get("postal_code")
    prefix = state.get("member_id")
    providers = []

    if "bcbs" in insurance or "blue" in insurance:
        print("🔷 Fetching BCBS providers dynamically...")
        providers = await get_bcbs_providers_live(
            postal_code=postal,
            prefix=prefix,
            specialty=specialty,
            location=location,
            max_pages=1,
            headless=True,
        )
    else:
        print(f"⚠️ No automated provider lookup for {insurance}.")
        if os.path.exists("providers.csv"):
            with open("providers.csv", newline="", encoding="utf-8") as f:
                providers = list(csv.DictReader(f))
            print(f"📁 Loaded {len(providers)} providers from providers.csv")
        else:
            print("❌ No providers found.")
            return state

    state["providers"] = providers
    return state


# -----------------------------
# Step 3–4: Review search + summarization
# -----------------------------
def search_doctor_reviews(name, city, specialty):
    query = f"{name} {city} {specialty} reviews site:healthgrades.com OR site:vitals.com OR site:zocdoc.com OR site:ratemds.com"
    print(f"🌐 Searching reviews for {name}...")
    try:
        resp = tavily.search(query=query, max_results=8)
        return [{"title": r["title"], "url": r["url"], "snippet": r["content"]} for r in resp.get("results", [])]
    except Exception as e:
        print(f"⚠️ Tavily error: {e}")
        return []


def summarize_reviews(name, specialty, city, reviews, symptom: Optional[str] = None):
    if not reviews:
        return {"name": name, "sentiment": 0, "review_count": 0, "summary": "No reviews found."}

    site_text = "\n\n".join([f"{r['title']}\n{r['snippet']}" for r in reviews])
    symptom_context = f"The patient is seeking help for '{symptom}'.\n" if symptom else ""
    prompt = f"""
{symptom_context}
Summarize these patient reviews for Dr. {name}, a {specialty} in {city}.
Return strictly in the following format:
Summary: ...
Score: X/10
Estimated Reviews: Y
Reason: ...
Reviews:
{site_text}
"""
    try:
        resp = llm.invoke(prompt)
        text = resp.content.strip() if hasattr(resp, "content") else str(resp)
        score_match = re.search(r"Score:\s*(\d+(?:\.\d+)?)", text)
        reviews_match = re.search(r"Estimated Reviews:\s*(\d+)", text)
        sentiment = float(score_match.group(1)) if score_match else 0
        review_count = int(reviews_match.group(1)) if reviews_match else len(reviews)
        print(f"\n🧠 Summary for {name}:\n{text}\n{'-'*70}")
        return {"name": name, "sentiment": sentiment, "review_count": review_count, "summary": text}
    except Exception as e:
        print(f"⚠️ Summarization error for {name}: {e}")
        return {"name": name, "sentiment": 0, "review_count": 0, "summary": "Error"}


# -----------------------------
# Step 5: Analysis and scoring
# -----------------------------
async def analyze_and_score(state: GraphState):
    providers = state.get("providers", [])
    if not providers:
        print("❌ No providers to analyze.")
        return state

    summaries = []
    for p in providers:
        reviews = search_doctor_reviews(p["Name"], state["location"], p["Specialty"])
        summaries.append(
            summarize_reviews(p["Name"], p["Specialty"], state["location"], reviews, symptom=state["symptom"])
        )

    compute_final_scores(providers, summaries, symptom=state["symptom"])

    for f in glob.glob("*.html") + glob.glob("*.csv"):
        try:
            os.remove(f)
        except Exception as e:
            print(f"⚠️ Could not delete {f}: {e}")
    return state


# -----------------------------
# LangGraph orchestration
# -----------------------------
graph = StateGraph(GraphState)
graph.add_node("GetUserInfo", get_user_info)
graph.add_node("FindProviders", find_providers)
graph.add_node("AnalyzeAndScore", analyze_and_score)
graph.add_edge(START, "GetUserInfo")
graph.add_edge("GetUserInfo", "FindProviders")
graph.add_edge("FindProviders", "AnalyzeAndScore")
graph.add_edge("AnalyzeAndScore", END)
app = graph.compile()


# -----------------------------
# Runner
# -----------------------------
async def run():
    await app.ainvoke({})

if __name__ == "__main__":
    asyncio.run(run())
