import os
from langchain_openai import ChatOpenAI

def get_nemotron():
    """Return a LangChain-compatible LLM client using OpenRouter + Nemotron."""
    llm = ChatOpenAI(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.getenv("OPEN_AI_API_KEY"),
        model_name="nvidia/nemotron-nano-9b-v2",
        temperature=0.3,
        max_tokens=800,
    )
    return llm
