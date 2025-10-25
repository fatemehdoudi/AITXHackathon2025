from langchain_openai import ChatOpenAI

def get_nemotron():
    """Return a LangChain-compatible LLM client using OpenRouter + Nemotron."""
    llm = ChatOpenAI(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key="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",
        model_name="nvidia/nemotron-nano-9b-v2",
        temperature=0.3,
        max_tokens=800,
    )
    return llm
