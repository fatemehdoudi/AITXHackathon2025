# insurance_network_search.py
from typing import Dict, Any
from insurance_portal_subfunctions import (
    find_bcbs_portal,
)
from tavily import TavilyClient
import os

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

async def find_portal(state: Dict[str, Any]) -> Dict[str, Any]:
    insurance = state.get("insurance", "").lower()

    print(f"🔍 Finding portal for insurance: {insurance}")

    if "blue cross" in insurance or "bcbs" in insurance:
        state.setdefault("postal_code", "77840")
        state.setdefault("prefix", "zgp")
        return find_bcbs_portal(state)