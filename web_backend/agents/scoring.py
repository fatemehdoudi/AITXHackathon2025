import math, re
from typing import Optional
from models import get_nemotron

llm = get_nemotron()

# -----------------------------
# Alignment reward computation
# -----------------------------
def compute_alignment_reward(specialty: str, symptom: Optional[str]) -> float:
    """Use LLM to check if specialty fits the symptom; return multiplier."""
    if not symptom:
        return 1.0
    prompt = f"""
You are a medical expert.
Is the specialty "{specialty}" appropriate for treating or diagnosing the symptom/disease "{symptom}"?
Answer with one word only: YES, MAYBE, or NO.
"""
    try:
        resp = llm.invoke(prompt)
        answer = resp.content.strip().upper() if hasattr(resp, "content") else str(resp).upper()
        if answer.startswith("YES"):
            return 1.10
        elif answer.startswith("MAYBE"):
            return 1.05
        else:
            return 1.0
    except Exception as e:
        print(f"⚠️ Alignment check failed for {specialty}: {e}")
        return 1.0


# -----------------------------
# Distance extraction helper
# -----------------------------
def extract_distance(address: str) -> Optional[float]:
    """Extract distance in miles from address text (e.g., '2.3 miles')."""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*miles", address, re.IGNORECASE)
    return float(match.group(1)) if match else None


# -----------------------------
# Distance scoring function
# -----------------------------
def distance_penalty(distance: float) -> float:
    """
    Apply distance penalty:
      - 0–10 miles → full score (10/10)
      - 10–30 miles → linearly reduced
      - >30 miles → minimum score (0)
    """
    if distance <= 10:
        return 10.0
    elif distance <= 30:
        # Linearly drop from 10 to 0 as distance goes from 10 to 30 miles
        return round(10 - ((distance - 10) / 20) * 10, 2)
    else:
        return 0.0


# -----------------------------
# Composite scoring
# -----------------------------
def compute_final_scores(providers, summaries, symptom: Optional[str] = None):
    """Combine sentiment, review volume, distance, and alignment into final score."""
    results = []
    for p in providers:
        s = next((x for x in summaries if x["name"] == p["Name"]), None)
        if not s:
            continue

        sentiment = s["sentiment"]
        reviews = s["review_count"]
        distance = extract_distance(p["Address"]) or 10.0  # Default 10mi if missing

        # Normalized review score (logarithmic scaling)
        review_score = min(1, math.log(1 + reviews) / math.log(1 + 50)) * 10

        # New distance score (flat under 10mi, penalty beyond)
        distance_score = distance_penalty(distance)

        # Weighted composite
        base_score = 0.5 * sentiment + 0.3 * review_score + 0.2 * distance_score

        # Add alignment multiplier
        align_multiplier = compute_alignment_reward(p["Specialty"], symptom)
        final_score = round(base_score * align_multiplier, 2)

        results.append({
            "Name": p["Name"],
            "FinalScore": final_score,
            "Sentiment": sentiment,
            "Reviews": reviews,
            "Distance(mi)": distance,
            "DistanceScore": distance_score,
            "AlignmentBonus": align_multiplier,
        })

    ranked = sorted(results, key=lambda x: x["FinalScore"], reverse=True)

    # Pretty-print results
    print("\n🏁 Final Doctor Ranking (with alignment & distance penalty):\n")
    for i, r in enumerate(ranked, 1):
        bonus = f" (x{r['AlignmentBonus']})" if r['AlignmentBonus'] > 1 else ""
        print(
            f"{i}. {r['Name']} — Score {r['FinalScore']}{bonus} "
            f"(Sentiment {r['Sentiment']}/10, Reviews {r['Reviews']}, "
            f"Distance {r['Distance(mi)']} mi)"
        )
    print("=" * 70)

    return ranked
