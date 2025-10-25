# bcbs_scraper.py

import csv
import urllib.parse
from playwright.async_api import async_playwright


async def get_bcbs_providers_live(postal_code, prefix, specialty, location, max_pages=1, headless=True):
    """
    Extract BCBS provider info dynamically using Playwright.
    Returns a list of provider dictionaries.
    """
    encoded_loc = urllib.parse.quote(location)
    encoded_spec = urllib.parse.quote(specialty)

    base_url = (
        f"https://provider.bcbs.com/app/public/#/one/"
        f"city=&state=&postalCode={postal_code}&country=&insurerCode=BCBSA_I"
        f"&brandCode=BCBSANDHF&alphaPrefix={prefix.lower()}&bcbsaProductId"
        f"/search/alphaPrefix={prefix.upper()}"
        f"&isPromotionSearch=true&location={encoded_loc}&radius=25"
        f"&searchCategory=SPECIALTY&query={encoded_spec}"
    )

    providers = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        for i in range(1, max_pages + 1):
            url = f"{base_url}&page={i}"
            print(f"🌐 Loading BCBS page {i}: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)

            try:
                await page.wait_for_selector('[data-test="provider-card"]', timeout=15000)
            except Exception:
                print(f"⚠️ No provider cards found on page {i}.")
                continue

            cards = await page.eval_on_selector_all(
                '[data-test="provider-card"]',
                """
                cards => cards.map(card => {
                    const nameEl = card.querySelector('[data-test="provider-r-card-header-name"], h2, a');
                    const specEl = card.querySelector('[data-test="specialties"]');
                    const addrEl = card.querySelector('address');
                    const phoneEl = card.querySelector('a[href^="tel:"]');
                    return {
                        Name: nameEl ? nameEl.textContent.trim() : "N/A",
                        Specialty: specEl ? specEl.textContent.trim() : "N/A",
                        Address: addrEl ? addrEl.textContent.trim().replace(/\\s+/g, ' ') : "N/A",
                        Phone: phoneEl ? phoneEl.textContent.trim() : "N/A"
                    };
                })
                """,
            )
            print(f"✅ Extracted {len(cards)} providers from page {i}")
            providers.extend(cards)

        await browser.close()

    # Save for debug/logging
    if providers:
        with open("bcbs_live_providers.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=providers[0].keys())
            writer.writeheader()
            writer.writerows(providers)
        print(f"💾 Saved {len(providers)} providers → bcbs_live_providers.csv")
    else:
        print("⚠️ No providers found.")

    return providers
