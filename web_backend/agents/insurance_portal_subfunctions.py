# insurance_portal_subfunctions.py
from typing import Dict, Any

def find_bcbs_portal(state: Dict[str, Any]) -> Dict[str, Any]:
    """Construct BCBS provider finder URL using postal code and prefix."""
    postal = str(state.get("postal_code", ""))
    prefix = str(state.get("prefix", "")).lower() or "zgp"
    brand = state.get("brand_code", "BCBSANDHF")

    url = (
        f"https://provider.bcbs.com/app/public/#/one/"
        f"city=&state=&postalCode={postal}"
        f"&country=&insurerCode=BCBSA_I"
        f"&brandCode={brand}"
        f"&alphaPrefix={prefix}"
        f"&bcbsaProductId"
    )

    state["portal_links"] = [{
        "title": "Blue Cross Blue Shield Provider Finder",
        "url": url
    }]
    print(f"✅ BCBS portal constructed: {url}")
    return state
