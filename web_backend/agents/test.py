# test.py
# Full script: Playwright loads the page, closes the modal, saves HTML, parses providers, outputs CSV

from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
import pandas as pd
import time

URL = (
    "https://hcpdirectory.cigna.com/web/public/consumer/directory/doctors?"
    "searchTerm=Cardiologist&providerGroupCodes=P&categoryId=15930&latitude=30.617"
    "&longitude=-96.312&city=College%20Station&stateCode=TX&country=US&zipCode=77840"
    "&searchLocation=College%20Station,%20TX%2077840&searchCategoryType=doctor-type"
    "&medicalProductCode=PPO&medicalEcnCode=NN001&suppressResponseCode=false"
    "&apiSource=public-provider-lambda&resultTitle=Cardiologist&consumerCode=HDC001"
)

# ---------------------------------------------------------------------
# STEP 1 — Use Playwright to get rendered HTML and close modal
# ---------------------------------------------------------------------

def fetch_and_clean_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # change to True for automation
        page = browser.new_page()

        print("Navigating to:", url)
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        time.sleep(8)  # allow JS to run, modal to appear

        # Try to close modal
        try:
            page.wait_for_selector("button[data-test-id='btnClose']", timeout=8000)
            page.click("button[data-test-id='btnClose']")
            print("✅ Modal closed using [data-test-id='btnClose']")
        except TimeoutError:
            try:
                page.click("button.cml-btn-close", timeout=3000)
                print("✅ Modal closed using [.cml-btn-close]")
            except TimeoutError:
                print("⚠️ No modal detected, continuing without close click.")
                # fallback: force remove if modal exists
                page.evaluate("""
                    for (const sel of ['.modal', '.popup', '.overlay', '.important-messages',
                                       '.cdk-overlay-container', '.mat-dialog-container']) {
                        const el = document.querySelector(sel);
                        if (el) el.remove();
                    }
                """)

        time.sleep(1)  # let DOM settle

        html = page.content()
        with open("cigna_clean.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("💾 Saved HTML to cigna_clean.html")

        browser.close()
    return html

# ---------------------------------------------------------------------
# STEP 2 — Parse HTML with BeautifulSoup
# ---------------------------------------------------------------------

def parse_provider_list(html):
    soup = BeautifulSoup(html, "html.parser")
    providers = []

    for container in soup.find_all("div", {"data-test-id": "listings-provider-container"}):
        # Provider name
        name_tag = container.find("a", {"data-test-id": "link-provider-name"})
        name = name_tag.get_text(strip=True) if name_tag else None

        # Address
        addr_tag = container.find("span", {"data-test-id": "listings-business-address"})
        address = addr_tag.get_text(strip=True) if addr_tag else None

        # Phone
        phone_tag = container.find("a", {"data-test-id": "link-phone-number"})
        phone = phone_tag.get_text(strip=True) if phone_tag else None

        # Specialty (first one)
        specialty_tag = container.find("span", {"data-test-id": "listings-specialty-content"})
        specialty = specialty_tag.get_text(strip=True) if specialty_tag else None

        # All hospital names (usually after specialty)
        hospitals = [
            h.get_text(strip=True)
            for h in container.find_all("span", {"data-test-id": "listings-specialty-content"})
        ][1:]  # skip first (specialty)

        providers.append({
            "name": name,
            "address": address,
            "phone": phone,
            "specialty": specialty,
            "hospitals": ", ".join(hospitals) if hospitals else None,
        })

    return providers

# ---------------------------------------------------------------------
# STEP 3 — Save to CSV and print
# ---------------------------------------------------------------------

def save_and_print(providers):
    df = pd.DataFrame(providers)
    df.to_csv("cigna_providers.csv", index=False)
    print("\n✅ Extracted", len(df), "providers. Saved to cigna_providers.csv.\n")
    for p in providers:
        print(f"Name: {p['name']}")
        print(f"  Address: {p['address']}")
        print(f"  Phone: {p['phone']}")
        print(f"  Specialty: {p['specialty']}")
        if p['hospitals']:
            print(f"  Hospitals: {p['hospitals']}")
        print("-" * 60)

# ---------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------

if __name__ == "__main__":
    html = fetch_and_clean_page(URL)
    providers = parse_provider_list(html)
    save_and_print(providers)
