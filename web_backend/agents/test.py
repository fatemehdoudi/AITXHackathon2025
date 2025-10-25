# test_reviews.py
"""
Test script: searches for online reviews for a few doctors and summarizes them.
Uses Tavily for web search and Nemotron for LLM summarization.
"""

import os
from tavily import TavilyClient
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# --- ✅ Set up API keys ---
os.environ["TAVILY_API_KEY"] = "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"
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

# --- 🔍 Step 1: Search for reviews ---
def search_doctor_reviews(name, city, specialty):
    """Search Google-like sources for doctor reviews."""
    query = f"{name} {city} {specialty} site:healthgrades.com OR site:vitals.com OR site:zocdoc.com OR site:ratemds.com"
    print(f"🌐 Searching reviews for {name} ...")
    try:
        resp = tavily.search(query=query, max_results=3)
        return [
            {"title": r["title"], "url": r["url"], "snippet": r["content"]}
            for r in resp.get("results", [])
        ]
    except Exception as e:
        print(f"⚠️ Tavily error for {name}: {e}")
        return []


# --- 🧠 Step 2: Summarize with LLM ---
def summarize_reviews(name, specialty, city, reviews):
    """Use Nemotron to summarize reviews."""
    if not reviews:
        return {"name": name, "summary": "No reviews found.", "score": 0}

    reviews_text = "\n\n".join([f"{r['title']}\n{r['snippet']}" for r in reviews])
    prompt = f"""
You are a medical review analysis agent.

Summarize the following reviews about Dr. {name}, a {specialty} in {city}.
Then provide:
1. A concise summary of patient sentiment.
2. A 1–10 reputation score (10 = excellent, 1 = poor).
3. One-sentence justification for the score.

Reviews:
{reviews_text}
"""

    try:
        resp = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2",
            messages=[{"role": "user", "content": prompt}],
        )
        result = resp.choices[0].message.content
        print(f"🧠 Summary for {name}:\n{result}\n")
        return {"name": name, "summary": result}
    except Exception as e:
        print(f"⚠️ LLM error for {name}: {e}")
        return {"name": name, "summary": "Error during LLM summarization.", "score": 0}


# --- 🚀 Step 3: Run a test loop ---
if __name__ == "__main__":
    test_doctors = [
        {"name": "Dr. Rachel R. Moore", "city": "Austin, TX", "specialty": "Dermatology"},
        {"name": "Dr. Emily Stewart", "city": "College Station, TX", "specialty": "Dermatology"},
    ]

    all_summaries = []

    for doc in test_doctors:
        reviews = search_doctor_reviews(doc["name"], doc["city"], doc["specialty"])
        summary = summarize_reviews(doc["name"], doc["specialty"], doc["city"], reviews)
        all_summaries.append(summary)

    print("\n=== FINAL SUMMARIES ===")
    for s in all_summaries:
        print(f"👩‍⚕️ {s['name']} → {s['summary'][:400]}...\n")
