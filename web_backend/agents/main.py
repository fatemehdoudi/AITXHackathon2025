"""
Enhanced pipeline:
1. Collect BCBS providers dynamically
2. Search and summarize reviews (LLM sentiment + count)
3. Extract distance from address
4. Compute final weighted score
5. Rank all doctors 1–N
"""

import asyncio, os, csv, math, re
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI

# -----------------------------
# Setup
# -----------------------------
load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPEN_AI_API_KEY"))


# -----------------------------
# State
# -----------------------------
class GraphState(TypedDict):
    insurance: Optional[str]
    specialty: Optional[str]
    location: Optional[str]
    postal_code: Optional[str]
    providers: Optional[list]


# -----------------------------
# Step 1: Get user info
# -----------------------------
async def get_user_info(state: GraphState):
    print("🧾 Collecting user info...")
    state["insurance"] = "Blue Cross Blue Shield"
    state["specialty"] = "Dermatology"
    state["location"] = "College Station, TX 77840"
    state["postal_code"] = "77840"
    print(f"User Info: {state}")
    return state


# -----------------------------
# Step 2: Get BCBS providers
# -----------------------------
async def get_bcbs_providers_live(postal_code, prefix, specialty, location, max_pages=1, headless=True):
    """Extract BCBS provider info dynamically."""
    import urllib.parse
    encoded_loc = urllib.parse.quote(location)
    encoded_spec = urllib.parse.quote(specialty)

    base_url = (
        f"https://provider.bcbs.com/app/public/#/one/"
        f"city=&state=&postalCode={postal_code}&country=&insurerCode=BCBSA_I"
        f"&brandCode=BCBSANDHF&alphaPrefix={prefix.lower()}&bcbsaProductId"
        f"/search/alphaPrefix={prefix.upper()}"
        f"&isPromotionSearch=true&location={encoded_loc}&radius=25"
        f"&searchCategory=SPECIALTY&query={encoded_spec}"
    )

    providers = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        for i in range(1, max_pages + 1):
            url = f"{base_url}&page={i}"
            print(f"🌐 Loading BCBS page {i}: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_selector('[data-test="provider-card"]', timeout=15000)

            cards = await page.eval_on_selector_all(
                '[data-test="provider-card"]',
                """
                cards => cards.map(card => {
                    const nameEl = card.querySelector('[data-test="provider-r-card-header-name"], h2, a');
                    const specEl = card.querySelector('[data-test="specialties"]');
                    const addrEl = card.querySelector('address');
                    const phoneEl = card.querySelector('a[href^="tel:"]');
                    return {
                        Name: nameEl ? nameEl.textContent.trim() : "N/A",
                        Specialty: specEl ? specEl.textContent.trim() : "N/A",
                        Address: addrEl ? addrEl.textContent.trim().replace(/\\s+/g, ' ') : "N/A",
                        Phone: phoneEl ? phoneEl.textContent.trim() : "N/A"
                    };
                })
                """,
            )

            print(f"✅ Extracted {len(cards)} providers from page {i}")
            providers.extend(cards)

        await browser.close()

    if providers:
        with open("bcbs_live_providers.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=providers[0].keys())
            writer.writeheader()
            writer.writerows(providers)
        print(f"💾 Saved {len(providers)} providers → bcbs_live_providers.csv")
    else:
        print("⚠️ No providers found.")
    return providers


# -----------------------------
# Step 3: Reviews + Summarization
# -----------------------------
def search_doctor_reviews(name, city, specialty):
    query = (
        f"{name} {city} {specialty} reviews "
        "site:healthgrades.com OR site:vitals.com OR site:zocdoc.com OR site:ratemds.com"
    )
    print(f"🌐 Searching reviews for {name} ...")
    try:
        resp = tavily.search(query=query, max_results=8)
        results = [
            {"title": r["title"], "url": r["url"], "snippet": r["content"]}
            for r in resp.get("results", [])
        ]
        print(f"✅ Found {len(results)} review pages.")
        return results
    except Exception as e:
        print(f"⚠️ Tavily error for {name}: {e}")
        return []


def summarize_reviews(name, specialty, city, reviews):
    """Summarize and extract sentiment + review count."""
    if not reviews:
        return {"name": name, "summary": "No reviews found.", "sentiment": 0, "review_count": 0}

    site_text = "\n\n".join([f"{r['title']}\n{r['snippet']}" for r in reviews])
    prompt = f"""
Summarize these reviews for Dr. {name}, a {specialty} in {city}.
Provide:
- A short summary of patient sentiment.
- A numeric 1–10 reputation score.
- The approximate number of distinct reviews mentioned (if unclear, estimate from snippets).

Format exactly as:
Summary: ...
Score: X/10
Estimated Reviews: Y
Reason: ...
Reviews:
{site_text}
"""
    try:
        resp = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2",
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()
        print(f"\n🧠 Review summary for {name}:\n{text}\n{'-'*70}")

        # Extract sentiment score and estimated review count
        score_match = re.search(r"Score:\s*(\d+(?:\.\d+)?)", text)
        reviews_match = re.search(r"Estimated Reviews:\s*(\d+)", text)

        sentiment = float(score_match.group(1)) if score_match else 0
        review_count = int(reviews_match.group(1)) if reviews_match else len(reviews)

        return {
            "name": name,
            "summary": text,
            "sentiment": sentiment,
            "review_count": review_count,
        }
    except Exception as e:
        print(f"⚠️ LLM summarization error for {name}: {e}")
        return {"name": name, "summary": "Error", "sentiment": 0, "review_count": 0}


# -----------------------------
# Step 4: Distance Parsing
# -----------------------------
def extract_distance(address):
    """Parse distance in miles from address string like '... • 3.1 miles'."""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*miles", address)
    return float(match.group(1)) if match else None


# -----------------------------
# Step 5: Composite Scoring
# -----------------------------
def compute_final_scores(providers, summaries):
    """Combine sentiment, review count, and distance."""
    results = []
    for p in providers:
        summary = next((s for s in summaries if s["name"] == p["Name"]), None)
        if not summary:
            continue

        sentiment = summary["sentiment"]
        reviews = summary["review_count"]
        distance = extract_distance(p["Address"]) or 10.0

        review_score = min(1, math.log(1 + reviews) / math.log(1 + 50)) * 10
        distance_score = max(0, (10 - min(distance, 10)))  # closer = higher

        final_score = round(0.5 * sentiment + 0.3 * review_score + 0.2 * distance_score, 2)

        results.append({
            "Name": p["Name"],
            "Sentiment": sentiment,
            "Reviews": reviews,
            "Distance(mi)": distance,
            "FinalScore": final_score,
        })

    ranked = sorted(results, key=lambda x: x["FinalScore"], reverse=True)
    print("\n🏁 Final Multi-Factor Ranking:\n")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. {r['Name']} — Final Score: {r['FinalScore']} (Sentiment {r['Sentiment']}/10, Reviews {r['Reviews']}, {r['Distance(mi)']} mi)")
    print("=" * 70)

    return ranked


# -----------------------------
# Step 6: Node Integration
# -----------------------------
async def find_bcbs_providers(state: GraphState):
    if "blue" not in state.get("insurance", "").lower():
        print("⚠️ Currently supports only BCBS.")
        return state

    prefix = "ZGP"
    print(f"🔎 Searching BCBS with prefix {prefix} ...")

    providers = await get_bcbs_providers_live(
        postal_code=state["postal_code"],
        prefix=prefix,
        specialty=state["specialty"],
        location=state["location"],
        max_pages=1,
        headless=True,
    )
    state["providers"] = providers

    summaries = []
    for p in providers[:3]:  # limit for testing
        reviews = search_doctor_reviews(p["Name"], state["location"], p["Specialty"])
        summaries.append(summarize_reviews(p["Name"], p["Specialty"], state["location"], reviews))

    compute_final_scores(providers, summaries)
    return state


# -----------------------------
# Step 7: LangGraph Build
# -----------------------------
graph = StateGraph(GraphState)
graph.add_node("GetUserInfo", get_user_info)
graph.add_node("FindBCBSProviders", find_bcbs_providers)
graph.add_edge(START, "GetUserInfo")
graph.add_edge("GetUserInfo", "FindBCBSProviders")
graph.add_edge("FindBCBSProviders", END)
app = graph.compile()


# -----------------------------
# Step 8: Run
# -----------------------------
async def run():
    result = await app.ainvoke({})
    print("\n=== FINAL OUTPUT ===")
    if result.get("providers"):
        for p in result["providers"][:5]:
            print(f"- {p['Name']} | {p['Specialty']} | {p['Address']} | {p['Phone']}")


if __name__ == "__main__":
    asyncio.run(run())
