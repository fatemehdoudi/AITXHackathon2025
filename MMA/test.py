# nemotron_test_graph.py
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from models import get_nemotron

llm = get_nemotron()

class GraphState(TypedDict):
    nemotron_test: str

async def summarize_test(state: GraphState):
    print("Invoking Nemotron...")
    msg = llm.invoke("Summarize why Nemotron is suitable for agent workflows.")
    state["nemotron_test"] = msg.content
    print("Nemotron replied:", msg.content[:200], "...")
    return state

graph = StateGraph(GraphState)
graph.add_node("SummarizeTest", summarize_test)
graph.add_edge(START, "SummarizeTest")   # ✅ entrypoint
graph.add_edge("SummarizeTest", END)

app = graph.compile()

async def run():
    result = await app.ainvoke({})
    print("\n=== FINAL OUTPUT ===")
    print(result["nemotron_test"])

if __name__ == "__main__":
    asyncio.run(run())
