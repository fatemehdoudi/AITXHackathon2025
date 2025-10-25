from tavily import TavilyClient
import os
from state_schema import GraphState


tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

async def find_portal(state: GraphState):
    print("🌐 Searching for insurance portal...")

    insurance = state.get("insurance", "")
    query = f"{insurance} find a doctor site:{insurance.split()[0].lower()}.com OR site:{insurance.split()[0].lower()}.org"

    try:
        response = tavily.search(query=query, max_results=5)
        results = [
            {"title": r["title"], "url": r["url"], "snippet": r["content"]}
            for r in response.get("results", [])
        ]
        # Filter for "find a doctor" or "provider search" links
        portals = [r for r in results if "find a doctor" in r["title"].lower() or "provider" in r["title"].lower()]
        state["portal_links"] = portals
        print(f"✅ Found {len(portals)} portal(s).")
        for p in portals[:3]:
            print(f" - {p['title']} → {p['url']}")
    except Exception as e:
        print(f"⚠️ Tavily search error: {e}")
        state["portal_links"] = []

    return state

