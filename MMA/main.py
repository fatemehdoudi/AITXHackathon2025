# nemotron_test_graph.py
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from models import get_nemotron
from typing import TypedDict, Optional

llm = get_nemotron()

class GraphState(TypedDict):
    insurance: Optional[str]
    condition: Optional[str]
    location: Optional[str]
    nemotron_test: Optional[str]

async def get_user_input(state: GraphState):
    print("Collecting user info...")
    state["insurance"] = "Aetna PPO"
    state["condition"] = "eczema"
    state["location"] = "Austin, TX"
    print(f"User Input: {state}")
    return state

async def summarize_test(state: GraphState):
    print("Invoking Nemotron...")

    insurance = state.get("insurance", "unknown insurance")
    condition = state.get("condition", "unknown condition")
    location = state.get("location", "unknown location")

    prompt = f"""
    You are an intelligent medical assistant.
    A patient with {insurance} insurance is looking for a doctor in {location}
    who can treat {condition}.
    
    Briefly summarize what kind of specialists or clinics they should search for,
    and what criteria (reviews, in-network, expertise) they should consider.
    """

    msg = llm.invoke(prompt)
    state["nemotron_test"] = msg.content
    print("Nemotron replied:", msg.content[:200], "...")
    return state


graph = StateGraph(GraphState)
graph.add_node("GetUserInput", get_user_input)
graph.add_node("SummarizeTest", summarize_test)

graph.add_edge(START, "GetUserInput")
graph.add_edge("GetUserInput", "SummarizeTest")
graph.add_edge("SummarizeTest", END)

app = graph.compile()

async def run():
    result = await app.ainvoke({})
    print("\n=== FINAL OUTPUT ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(run())
