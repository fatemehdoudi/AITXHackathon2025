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
    https://provider.bcbs.com/app/public/#/one/city=&state=&postalCode=77840&country=&insurerCode=BCBSA_I&brandCode=BCBSANDHF&alphaPrefix=zgp&bcbsaProductId/search/alphaPrefix=ZGP&isPromotionSearch=true&location=College%2520Station%252C%2520TX%252077840&page=1&query=dermatology&radius=25&searchCategory=SPECIALTY

    state["portal_links"] = [{
        "title": "Blue Cross Blue Shield Provider Finder",
        "url": url
    }]
    print(f"✅ BCBS portal constructed: {url}")
    return state
