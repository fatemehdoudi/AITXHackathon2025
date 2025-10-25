# test_reviews_detailed.py
"""
Enhanced test script:
- Searches multiple review sites (Healthgrades, Vitals, Zocdoc, RateMDs, Google Maps)
- Summarizes reviews from each site individually
- Then provides an overall reputation summary + score
- Finally, compares all doctors and recommends one
"""

import os
from tavily import TavilyClient
from openai import OpenAI
from dotenv import load_dotenv

# --- 🔧 Load environment variables ---
load_dotenv()

# --- ✅ Set up API keys ---
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENAI_API_KEY"))


# --- 🔍 Step 1: Search for reviews ---
def search_doctor_reviews(name, city, specialty):
    """
    Search Google, Healthgrades, Vitals, Zocdoc, RateMDs, and Google Maps for doctor reviews.
    Added 'Google Reviews' phrasing to improve recall from Tavily.
    """
    query = (
        f"{name} {city} {specialty} reviews OR 'Google Reviews' "
        "site:healthgrades.com OR site:vitals.com OR site:zocdoc.com "
        "OR site:ratemds.com OR site:google.com/maps/place OR site:google.com/search"
    )
    print(f"🌐 Searching reviews for {name} ...")
    try:
        resp = tavily.search(query=query, max_results=10)
        results = [
            {"title": r["title"], "url": r["url"], "snippet": r["content"]}
            for r in resp.get("results", [])
        ]
        print(f"✅ Found {len(results)} review pages.")
        return results
    except Exception as e:
        print(f"⚠️ Tavily error for {name}: {e}")
        return []


# --- 🧠 Step 2: Summarize reviews per website ---
def summarize_reviews_per_site(name, specialty, city, reviews):
    """LLM summarizes reviews from each site separately, then overall."""
    if not reviews:
        return {"name": name, "summary": "No reviews found.", "score": 0}

    grouped = {}
    for r in reviews:
        domain = r["url"].split("/")[2].replace("www.", "")
        grouped.setdefault(domain, []).append(r)

    site_summaries = []
    for domain, items in grouped.items():
        site_text = "\n\n".join([f"{i['title']}\n{i['snippet']}\nURL: {i['url']}" for i in items])
        prompt = f"""
Summarize patient feedback for Dr. {name}, a {specialty} in {city}, based on reviews from **{domain}**.

Give:
1. A short summary of patient sentiment (tone, key praise, main complaints).
2. A 1–10 rating for this site only.
3. One line justification for the rating.

Reviews:
{site_text}
"""
        try:
            resp = client.chat.completions.create(
                model="nvidia/nemotron-nano-9b-v2",
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.choices[0].message.content.strip()
            print(f"\n📄 {domain} Summary:\n{text}\n{'-'*70}")
            site_summaries.append(f"### {domain}\n{text}")
        except Exception as e:
            print(f"⚠️ Error summarizing {domain}: {e}")

    # Combine site summaries for final judgment
    combined_text = "\n\n".join(site_summaries)
    overall_prompt = f"""
You are an expert medical review aggregator.

You have these summaries from multiple websites about Dr. {name}, a {specialty} in {city}:

{combined_text}

Now:
1. Write one short final paragraph summarizing the overall reputation.
2. Provide an overall 1–10 reputation score.
3. Explain your reasoning in one line.
Return your response clearly formatted as:
"Summary: ...\nScore: X/10\nReason: ..."
"""
    try:
        resp = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2",
            messages=[{"role": "user", "content": overall_prompt}],
        )
        result = resp.choices[0].message.content
        print(f"\n🏁 Final Summary for {name}:\n{result}\n{'='*70}")
        return {"name": name, "summary": result}
    except Exception as e:
        print(f"⚠️ LLM overall error for {name}: {e}")
        return {"name": name, "summary": "Error during overall summarization."}


# --- 🧠 Step 3: Choose recommended doctor ---
def recommend_best_doctor(summaries):
    """Ask LLM to compare all doctors and recommend one."""
    combined_text = "\n\n".join([f"{s['name']}\n{s['summary']}" for s in summaries])
    prompt = f"""
You are a medical assistant comparing multiple doctors based on review summaries.

Here are the summaries and scores for each doctor:
{combined_text}

Task:
1. Identify which doctor you would recommend to a patient.
2. Explain your reasoning in 2–3 sentences.
3. End your answer with: "Recommended Doctor: [name]"
"""
    try:
        resp = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2",
            messages=[{"role": "user", "content": prompt}],
        )
        recommendation = resp.choices[0].message.content
        print(f"\n💡 Recommendation:\n{recommendation}\n{'#'*70}")
    except Exception as e:
        print(f"⚠️ LLM recommendation error: {e}")


# --- 🚀 Step 4: Run test ---
if __name__ == "__main__":
    test_doctors = [
        {"name": "Dr. Rachel R. Moore", "city": "Austin, TX", "specialty": "Dermatology"},
        {"name": "Dr. Emily Stewart", "city": "College Station, TX", "specialty": "Dermatology"},
    ]

    all_summaries = []
    for doc in test_doctors:
        reviews = search_doctor_reviews(doc["name"], doc["city"], doc["specialty"])
        summary = summarize_reviews_per_site(doc["name"], doc["specialty"], doc["city"], reviews)
        all_summaries.append(summary)

    recommend_best_doctor(all_summaries)
