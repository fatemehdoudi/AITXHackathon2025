from playwright.sync_api import sync_playwright
import urllib.parse

def build_bcbs_url(postal_code: str, prefix: str, specialty: str, location: str) -> str:
    base_url = "https://provider.bcbs.com/app/public/#/one/"
    encoded_location = urllib.parse.quote(location)
    return (
        f"{base_url}"
        f"city=&state=&postalCode={postal_code}&country=&insurerCode=BCBSA_I"
        f"&brandCode=BCBSANDHF&alphaPrefix={prefix.lower()}&bcbsaProductId"
        f"/search/alphaPrefix={prefix.upper()}"
        f"&isPromotionSearch=true"
        f"&location={encoded_location}"
        f"&page=1"
        f"&query={urllib.parse.quote(specialty)}"
        f"&radius=25"
        f"&searchCategory=SPECIALTY"
    )


def search_bcbs_doctors(postal_code, prefix, specialty, location, headless=True):
    """Load BCBS provider finder and extract visible doctor names."""
    url = build_bcbs_url(postal_code, prefix, specialty, location)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        print(f"🌐 Navigating to: {url}")
        page.goto(url)

        # wait until at least one provider result appears
        try:
            page.wait_for_selector("article, div[class*='provider-card']", timeout=20000)
            print("✅ Provider results loaded.")
        except:
            print("⚠️ Timed out waiting for provider results.")
            browser.close()
            return []

        # extract visible provider cards
        provider_cards = page.locator("article, div[class*='provider-card']")
        count = provider_cards.count()
        print(f"🔍 Found {count} provider cards.")

        doctors = []
        for i in range(min(count, 10)):  # limit to first 10
            name = None
            specialty_text = None
            address = None
            try:
                name = provider_cards.nth(i).locator("text=Dr").first.text_content()
            except:
                pass
            try:
                specialty_text = provider_cards.nth(i).locator("text=Specialty").first.text_content()
            except:
                pass
            try:
                address = provider_cards.nth(i).locator("text=Address").first.text_content()
            except:
                pass

            if name:
                doctors.append({
                    "name": name.strip(),
                    "specialty": specialty_text.strip() if specialty_text else specialty,
                    "address": address.strip() if address else location
                })

        browser.close()
        print(f"✅ Extracted {len(doctors)} doctors.")
        return doctors


# Example
if __name__ == "__main__":
    docs = search_bcbs_doctors(
        postal_code="77840",
        prefix="ZGP",
        specialty="Dermatology",
        location="College Station, TX 77840",
        headless=False
    )
    for d in docs:
        print(f"- {d['name']} ({d['specialty']}) — {d['address']}")
