# bcbs_scraper_fastscroll.py
from playwright.sync_api import sync_playwright
import urllib.parse
import time


def build_bcbs_url(postal_code: str, prefix: str, specialty: str, location: str) -> str:
    base = "https://provider.bcbs.com/app/public/#/one/"
    encoded_loc = urllib.parse.quote(location)
    return (
        f"{base}"
        f"city=&state=&postalCode={postal_code}&country=&insurerCode=BCBSA_I"
        f"&brandCode=BCBSANDHF&alphaPrefix={prefix.lower()}&bcbsaProductId"
        f"/search/alphaPrefix={prefix.upper()}"
        f"&isPromotionSearch=true"
        f"&location={encoded_loc}"
        f"&page=1"
        f"&query={urllib.parse.quote(specialty)}"
        f"&radius=25"
        f"&searchCategory=SPECIALTY"
    )


def search_bcbs_doctors(postal_code, prefix, specialty, location, max_results=50, headless=True):
    """Scrape BCBS provider list using headless browser scrolling."""
    url = build_bcbs_url(postal_code, prefix, specialty, location)
    print(f"🌐 Navigating to:\n{url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(4000)

        # Wait for initial provider elements
        try:
            page.wait_for_selector("article, div[data-test*='provider']", timeout=20000)
            print("✅ Provider results loaded.")
        except:
            print("⚠️ No provider results detected.")
            browser.close()
            return []

        # Scroll to bottom repeatedly to trigger dynamic loading
        prev_height = 0
        scroll_attempts = 0
        while scroll_attempts < 8:  # cap attempts
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(2.5)
            curr_height = page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                break
            prev_height = curr_height
            scroll_attempts += 1
        print(f"↕️ Scrolled {scroll_attempts} times to load full results.")

        # Extract visible provider cards
        cards = page.locator("article, div[data-test*='provider']")
        count = cards.count()
        print(f"🩺 Found {count} provider entries on screen.")

        doctors = []
        for i in range(min(count, max_results)):
            card = cards.nth(i)
            try:
                name = card.locator("h3, h2, div:has-text('MD')").first.text_content()
            except:
                name = "N/A"
            try:
                specialty_text = card.locator("text=Specialty").first.text_content()
            except:
                specialty_text = specialty
            try:
                address = card.locator("text=Address").first.text_content()
            except:
                address = location

            doctors.append({
                "name": name.strip() if name else "N/A",
                "specialty": specialty_text.strip() if specialty_text else specialty,
                "address": address.strip() if address else location
            })

        browser.close()
        print(f"✅ Extracted {len(doctors)} provider records.")
        return doctors


# Example
if __name__ == "__main__":
    results = search_bcbs_doctors(
        postal_code="77840",
        prefix="ZGP",
        specialty="Dermatology",
        location="College Station, TX 77840",
        max_results=25,
        headless=False  # set True for backend mode
    )

    print("\nTop Providers:")
    for d in results[:5]:
        print(f"- {d['name']} — {d['specialty']} — {d['address']}")
