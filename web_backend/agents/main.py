# main.py
import asyncio
import re
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from models import get_nemotron
from insurance_network_search import find_portal

class GraphState(TypedDict):
    insurance: Optional[str]
    insurance_id: Optional[str]
    prefix: Optional[str]
    postal_code: Optional[str]
    portal_links: Optional[List[Dict[str, str]]]
    nemotron_summary: Optional[str]

llm = get_nemotron()


async def get_user_input(state: GraphState) -> GraphState:
    print("🧾 Collecting user info...")
    state["insurance"] = "Blue Cross Blue Shield"
    state["insurance_id"] = "ZGP123456789"
    state["postal_code"] = "77840"

    match = re.match(r"([A-Za-z]{3})", state["insurance_id"] or "")
    state["prefix"] = match.group(1).upper() if match else None

    print(f"Insurance: {state['insurance']}")
    print(f"Insurance ID: {state['insurance_id']}")
    print(f"Extracted Prefix: {state['prefix']}")
    print(f"Postal Code: {state['postal_code']}")
    return state


async def summarize_portal(state: GraphState) -> GraphState:
    portals = state.get("portal_links", [])
    if not portals:
        state["nemotron_summary"] = "No portal links found."
        print("⚠️ No portals found to summarize.")
        return state

    links_text = "\n".join([f"{p['title']} - {p['url']}" for p in portals])
    prompt = f"""
    Given these links for {state['insurance']}, identify which one is the most reliable portal
    for finding in-network doctors or providers. Reply concisely with reasoning.
    {links_text}
    """

    msg = llm.invoke(prompt)
    state["nemotron_summary"] = msg.content
    print("🧠 Nemotron Summary:", msg.content[:200], "...")
    return state


# ------------------------------
# Build LangGraph
# ------------------------------
graph = StateGraph(GraphState)
graph.add_node("GetUserInput", get_user_input)
graph.add_node("FindPortal", find_portal)
graph.add_node("SummarizePortal", summarize_portal)

graph.add_edge(START, "GetUserInput")
graph.add_edge("GetUserInput", "FindPortal")
graph.add_edge("FindPortal", "SummarizePortal")
graph.add_edge("SummarizePortal", END)

app = graph.compile()


# ------------------------------
# Run the App
# ------------------------------
async def run():
    result = await app.ainvoke({})
    print("\n=== FINAL OUTPUT ===")
    for k, v in result.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    asyncio.run(run())