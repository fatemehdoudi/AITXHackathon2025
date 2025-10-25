# nemotron_test_graph.py
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from models import get_nemotron
from typing import TypedDict, Optional
from insurance_network_search import find_portal
from state_schema import GraphState


llm = get_nemotron()

async def get_user_input(state: GraphState):
    print("Collecting user info...")
    state["insurance"] = "Aetna PPO"
    print(f"User insurance: {state['insurance']}")
    return state


async def summarize_test(state: GraphState):
    portals = state.get("portal_links", [])
    if not portals:
        state["nemotron_summary"] = "No portals found."
        return state

    text = "\n".join([f"{p['title']} - {p['url']}" for p in portals])
    prompt = f"""
    Given these search results for {state['insurance']}, identify the official in-network provider portal.
    {text}
    Reply with the single most trustworthy link and why.
    """
    msg = llm.invoke(prompt)
    state["nemotron_summary"] = msg.content
    print("Nemotron Summary:", msg.content[:200], "...")
    return state


graph = StateGraph(GraphState)
graph.add_node("GetUserInput", get_user_input)
graph.add_node("FindPortal", find_portal)
graph.add_node("Summarize", summarize_test)

graph.add_edge(START, "GetUserInput")
graph.add_edge("GetUserInput", "FindPortal")
graph.add_edge("FindPortal", "Summarize")
graph.add_edge("Summarize", END)

app = graph.compile()


async def run():
    result = await app.ainvoke({})
    print("\n=== FINAL OUTPUT ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(run())
