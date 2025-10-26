import asyncio, os, csv, re, glob, hashlib, json, requests
from typing import TypedDict, Optional
from bs4 import BeautifulSoup
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from tavily import TavilyClient
from utils.bcbs_scraper import get_bcbs_providers_live
from models import get_nemotron
from scoring import compute_final_scores
from utils.utils import city_state_from_zip
from utils.utils import cleanup_temp_data

import json, re

# =========================================================
# Setup
# =========================================================
load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
llm = get_nemotron()

MAX_PROVIDERS = 7
MAX_CHARS = 15000
SITE_WEIGHT = 0.4
MODEL_WEIGHT = 0.6


# =========================================================
# Graph State
# =========================================================
class GraphState(TypedDict):
    insurance: Optional[str]
    specialty: Optional[str]
    location: Optional[str]
    postal_code: Optional[str]
    symptom: Optional[str]
    member_id: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    is_pediatric: Optional[bool]
    providers: Optional[list]


# =========================================================
# Helper: LLM reasoning
# =========================================================
def get_specialty_from_symptom(symptom_description: str, age: int, gender: str) -> str:
    pediatric_note = "The patient is a child (under 16)." if age < 16 else "The patient is an adult."
    prompt = f"""
    You are a medical triage assistant.
    Given this patient profile:

    Symptom: "{symptom_description}"
    Age: {age}
    Sex: {gender}
    Note: {pediatric_note}

    Suggest the most appropriate specialty that should evaluate this case.
    Return in strict JSON only:
    {{"recommended": "specialty"}}
    """
    try:
        resp = llm.invoke(prompt)
        text = resp.content.strip() if hasattr(resp, "content") else str(resp)
        match = re.search(r'"recommended"\s*:\s*"([^"]+)"', text)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"⚠️ Error inferring specialty: {e}")
    return "Internal Medicine"


def is_specialty_term(user_input: str) -> bool:
    prompt = f'Is "{user_input}" a valid medical specialty? Answer only YES or NO.'
    try:
        resp = llm.invoke(prompt)
        text = resp.content.strip().upper() if hasattr(resp, "content") else str(resp).upper()
        return text.startswith("YES")
    except Exception as e:
        print(f"⚠️ Error checking specialty: {e}")
        return False


# =========================================================
# Step 1: User info
# =========================================================
async def get_user_info(state: GraphState):
    print("🧾 Collecting user info...\n")

    user_input = input("🩺 Describe your main symptom or enter a specialty: ").strip()
    state["symptom"] = user_input

    try:
        age = int(input("🎂 Enter patient age: ").strip())
    except ValueError:
        age = 30
    gender = input("⚧️ Enter patient sex (Male/Female/Other): ").strip().capitalize() or "Unknown"
    state["age"] = age
    state["gender"] = gender
    state["is_pediatric"] = age < 16

    if is_specialty_term(user_input):
        state["specialty"] = user_input
    else:
        state["specialty"] = get_specialty_from_symptom(user_input, age, gender)

    insurance = input("🏥 Enter your insurance provider (currently only BCBS supported): ").strip()
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
    state["postal_code"] = postal_code

    # ✅ Auto-fill city/state if missing
    has_city = re.search(r"[A-Za-z]", location)
    if not has_city or not re.search(r",[ ]?[A-Za-z]{2}", location):
        city, st = city_state_from_zip(postal_code)
        if city and st:
            location = f"{city}, {st}"

    state["location"] = location

    print(f"\n✅ Summary of user input:")
    print(f" - Symptom: {state['symptom']}")
    print(f" - Age: {age} ({'Pediatric' if state['is_pediatric'] else 'Adult'})")
    print(f" - Gender: {gender}")
    print(f" - Specialty: {state['specialty']}")
    print(f" - Insurance: {state['insurance']}")
    print(f" - Member ID Prefix: {state.get('member_id', 'N/A')}")
    print(f" - Location: {state['location']}")
    print(f" - Postal Code: {state['postal_code']}\n{'-'*60}")
    return state


# =========================================================
# Step 2: Provider lookup
# =========================================================
async def find_providers(state: GraphState):
    insurance = state.get("insurance", "").lower()
    specialty = state.get("specialty")
    location = state.get("location")
    postal = state.get("postal_code")
    prefix = state.get("member_id")

    providers = []
    print(f"\n🔍 Finding providers for {specialty} ({insurance})...")

    if "bcbs" in insurance or "blue" in insurance:
        providers = await get_bcbs_providers_live(
            postal_code=postal,
            prefix=prefix,
            specialty=specialty,
            location=location,
            max_pages=1,
            headless=True,
        )
    else:
        if os.path.exists("providers.csv"):
            with open("providers.csv", newline="", encoding="utf-8") as f:
                providers = list(csv.DictReader(f))
        else:
            print("❌ No providers found.")
            return state

    print(f"✅ Found {len(providers)} providers.")
    for p in providers:
        p["alignment_multiplier"] = 1.2 if state["is_pediatric"] and "pediatric" in p.get("specialty", "").lower() else 1.0
    state["providers"] = providers
    return state


# =========================================================
# Step 3: Fetch & Save HTML
# =========================================================
def fetch_reviews(name, city, specialty):
    print(f"\n🌐 Fetching review pages for {name} — {specialty}, {city}")
    os.makedirs("doctor_pages", exist_ok=True)
    pages = {}

    site_domains = [
        "healthgrades.com/physician",
        "vitals.com/doctors",
        "ratemds.com/doctor-ratings",
    ]

    for site in site_domains:
        try:
            query = f"{name}, {city}, {specialty} site:{site}"
            print(f"🔍 Searching {site}...")
            resp = tavily.search(query=query, include_raw_content=True, max_results=10)

            if not resp.get("results"):
                print(f"  ⚠️ No results for {site}")
                continue

            result = next(
                (r for r in resp["results"]
                 if r.get("url", "").startswith(f"https://www.{site}") or
                    r.get("url", "").startswith(f"http://www.{site}") or
                    r.get("url", "").startswith(f"https://{site}")),
                resp["results"][0]
            )

            url = result.get("url", "")
            raw = result.get("raw_content") or result.get("content", "")

            if not raw and url:
                print(f"  ⚠️ Tavily missing content, fetching directly from {url}")
                try:
                    r = requests.get(
                        url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/122.0.0.0 Safari/537.36"
                            )
                        },
                        timeout=15,
                    )
                    if r.status_code == 200 and len(r.text) > 1000:
                        raw = r.text
                    else:
                        print(f"  ❌ Fallback fetch failed ({r.status_code})")
                        continue
                except Exception as e:
                    print(f"  ❌ Error fetching {url}: {e}")
                    continue

            if raw:
                hash_id = hashlib.sha256(url.encode()).hexdigest()[:8]
                safe_site = site.replace("/", "_").replace(":", "_")
                safe_name = re.sub(r"[^A-Za-z0-9 _.-]", "", name)
                filename = f"doctor_pages/{safe_name}_{safe_site}_{hash_id}.html"

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(raw)
                print(f"  💾 Saved HTML from {site} to {filename}")
                pages[site] = raw[:MAX_CHARS]
            else:
                print(f"  ⚠️ No usable HTML from {site}")

        except Exception as e:
            print(f"  ❌ Error while fetching {site}: {e}")
            continue

    if not pages:
        print("  ❌ No usable pages found across all sites.")
    return pages


# =========================================================
# Step 4: LLM-based review extraction
# =========================================================
def extract_relevant_chunks(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    matches = re.findall(
        r"((?:\d(?:\.\d)?)\s*(?:Star|Rating|ratings?)|based on\s*\d+\s*(?:reviews|ratings)|\d+\s*(?:patient\s+)?reviews?)",
        text,
        re.I,
    )
    if matches:
        chunks = []
        for m in matches:
            idx = text.lower().find(m.lower())
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(text), idx + 80)
                chunks.append(text[start:end])
        return " ... ".join(chunks)
    return text[:8000]


def llm_extract_review_data(html_content: str, site: str, name: str) -> dict:
    text = extract_relevant_chunks(html_content)
    prompt = f"""
You are reading reviews for {name} from {site}.
Extract three numbers:
1. total number of patient reviews,
2. average star rating (out of 5),
3. overall patient sentiment (1–10, 10 = very positive).

Return only JSON, no reasoning:
{{"reviews": int, "rating": float, "sentiment": float}}

Text:
{text}
"""
    try:
        resp = llm.invoke(prompt)
        text_out = resp.content if hasattr(resp, "content") else str(resp)
        print(f"      🧩 Raw LLM output from {site}:\n{text_out}\n")
        # Extract *only* the first valid JSON-like object
        match = re.search(r"\{[^{}]+\}", text_out, re.S)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # attempt to clean malformed output like trailing commas or explanations
                json_str = re.sub(r"[^{}:,0-9.\s\"\-a-zA-Z]", "", json_str)
                json_str = re.sub(r",\s*}", "}", json_str)
                try:
                    data = json.loads(json_str)
                except Exception:
                    return {"reviews": 0, "rating": 0.0, "sentiment": 5.0}
            return {
                "reviews": int(data.get("reviews", 0)),
                "rating": float(data.get("rating", 0.0)),
                "sentiment": float(data.get("sentiment", 5.0)),
            }

    except Exception as e:
        print(f"⚠️ LLM extraction failed for {site}: {e}")
    return {"reviews": 0, "rating": 0.0, "sentiment": 5.0}


# =========================================================
# Step 5: Doctor-level reasoning
# =========================================================
async def rag_analyze_doctor(name, specialty, city, symptom):
    pages = fetch_reviews(name, city, specialty)
    if not pages:
        return f"❌ No review pages found for {name}."

    total_reviews, weighted_sum = 0, 0.0
    total_site_rating, total_model_sentiment = 0.0, 0.0
    rating_count, sentiment_count = 0, 0
    site_lines = []

    for site, text in pages.items():
        print(f"\n   🌍 Processing {site} ({len(text)} chars)")
        data = llm_extract_review_data(text, site, name)
        num, site_rating, sentiment_score = data["reviews"], data["rating"], data["sentiment"]
        combined = round((site_rating * 2 * SITE_WEIGHT) + (sentiment_score * MODEL_WEIGHT), 2)
        total_reviews += num
        weighted_sum += combined * max(num, 1)
        if site_rating > 0:
            total_site_rating += site_rating
            rating_count += 1
        if sentiment_score > 0:
            total_model_sentiment += sentiment_score
            sentiment_count += 1
        site_lines.append(f"— {site}: ~{num} reviews, ⭐ {site_rating:.1f}/5, 🧠 {sentiment_score:.1f}/10, combined {combined:.1f}/10")

    avg_score = weighted_sum / max(total_reviews, 1)
    avg_rating = total_site_rating / max(rating_count, 1)
    avg_sentiment = total_model_sentiment / max(sentiment_count, 1)

    return (
        f"SUMMARY — {name} ({specialty}, {city})\n"
        f"Total reviews (all sites): ~{total_reviews}\n"
        f"Average ⭐ site rating: {avg_rating:.2f}/5\n"
        f"Average 🧠 sentiment: {avg_sentiment:.2f}/10\n"
        f"Overall blended score: ~{avg_score:.1f}/10\n"
        + "\n".join(site_lines)
    )


# =========================================================
# Step 6: Aggregate & Rank
# =========================================================
async def analyze_and_score(state: GraphState):
    providers = state.get("providers", [])
    if not providers:
        print("❌ No providers to analyze.")
        return state

    summaries = []
    for idx, p in enumerate(providers[:MAX_PROVIDERS], start=1):
        name = p.get("name") or p.get("Name")
        print(f"\n➡️ Doctor {idx}: {name}")
        summary = await rag_analyze_doctor(name, p.get("Specialty"), state["location"], state["symptom"])

        m_reviews = re.search(r"Total reviews.*?:\s*~(\d+)", summary)
        m_sent = re.search(r"Average 🧠 sentiment:\s*(\d+(?:\.\d+)?)", summary)
        m_rating = re.search(r"Average ⭐ site rating:\s*(\d+(?:\.\d+)?)", summary)
        m_score = re.search(r"Overall blended score:\s*~(\d+(?:\.\d+)?)", summary)

        p["review_count"] = int(m_reviews.group(1)) if m_reviews else 0
        p["sentiment"] = float(m_sent.group(1)) if m_sent else 0.0
        p["avg_rating"] = float(m_rating.group(1)) if m_rating else 0.0
        p["score"] = float(m_score.group(1)) if m_score else 0.0
        summaries.append(p)

    for p in providers:
        if "Name" in p and "name" not in p:
            p["name"] = p["Name"]

    ranked = compute_final_scores(providers, summaries, symptom=state["symptom"])
    cleanup_temp_data()
    return state


# =========================================================
# Graph Orchestration
# =========================================================
graph = StateGraph(GraphState)
graph.add_node("GetUserInfo", get_user_info)
graph.add_node("FindProviders", find_providers)
graph.add_node("AnalyzeAndScore", analyze_and_score)
graph.add_edge(START, "GetUserInfo")
graph.add_edge("GetUserInfo", "FindProviders")
graph.add_edge("FindProviders", "AnalyzeAndScore")
graph.add_edge("AnalyzeAndScore", END)
app = graph.compile()


# =========================================================
# Runner
# =========================================================
async def run():
    await app.ainvoke({})

if __name__ == "__main__":
    asyncio.run(run())
