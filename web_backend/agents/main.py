# main.py
import asyncio
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import glob
import csv
import os
import re
import urllib.parse
import time


# -----------------------------
# 1. Graph State Schema
# -----------------------------
class GraphState(TypedDict):
    insurance: Optional[str]
    specialty: Optional[str]
    location: Optional[str]
    postal_code: Optional[str]
    providers: Optional[list]


# -----------------------------
# 2. Get user input
# -----------------------------
async def get_user_info(state: GraphState):
    print("🧾 Collecting user info...")
    # For now, hardcode example — later we’ll make it interactive
    state["insurance"] = "Blue Cross Blue Shield"
    state["specialty"] = "Cardiology"
    state["location"] = "College Station, TX 77840"
    state["postal_code"] = "77840"
    print(f"User: {state}")
    return state


# -----------------------------
# 3. Fetch BCBS HTML pages
# -----------------------------

async def get_bcbs_html_multi(postal_code, prefix, specialty, location, max_pages=4, headless=True):
    """Fetch multiple BCBS result pages asynchronously and save HTML."""
    import urllib.parse, asyncio, time

    encoded_loc = urllib.parse.quote(location)
    encoded_spec = urllib.parse.quote(specialty)

    base_url = (
        f"https://provider.bcbs.com/app/public/#/one/"
        f"city=&state=&postalCode={postal_code}&country=&insurerCode=BCBSA_I"
        f"&brandCode=BCBSANDHF&alphaPrefix={prefix.lower()}&bcbsaProductId"
        f"/search/alphaPrefix={prefix.upper()}"
        f"&isPromotionSearch=true"
        f"&location={encoded_loc}"
        f"&radius=25"
        f"&searchCategory=SPECIALTY"
        f"&query={encoded_spec}"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        for i in range(1, max_pages + 1):
            url = f"{base_url}&page={i}"
            print(f"🌐 Loading page {i}: {url}")
            await page.goto(url)
            await page.wait_for_timeout(8000)
            html = await page.content()
            filename = f"bcbs_result_page{i}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ Saved {filename}")
            await asyncio.sleep(2)

        await browser.close()
    print("🎯 All pages saved.")


# -----------------------------
# 4. Parse BCBS HTML pages
# -----------------------------
def parse_all_bcbs_pages(delete_after=True):
    def parse_bcbs_html(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        doctors = []
        cards = soup.find_all("div", {"data-test": "provider-card"})

        for card in cards:
            name_tag = (
                card.find("h2", {"data-test": "provider-r-card-header-name"})
                or card.find("a", {"data-test": "provider-r-card-header-name"})
                or card.find("h2", string=re.compile(r"(MD|DO|PhD|NP)", re.I))
            )
            name = name_tag.get_text(strip=True) if name_tag else "N/A"

            specialty_tag = card.find("div", {"data-test": "specialties"})
            specialty = specialty_tag.get_text(strip=True) if specialty_tag else "N/A"

            address_tag = card.find("address", {"data-test": "provider-address"})
            address = address_tag.get_text(" ", strip=True) if address_tag else "N/A"

            phone_tag = card.find("a", href=lambda x: x and x.startswith("tel:"))
            phone = phone_tag.get_text(strip=True) if phone_tag else "N/A"

            doctors.append({
                "Name": name,
                "Specialty": specialty,
                "Address": address,
                "Phone": phone,
                "SourceFile": os.path.basename(file_path),
            })
        return doctors

    all_doctors = []
    html_files = sorted(glob.glob("bcbs_result_page*.html"))
    for file_path in html_files:
        print(f"🔍 Parsing {file_path} ...")
        docs = parse_bcbs_html(file_path)
        print(f"✅ Found {len(docs)} providers.")
        all_doctors.extend(docs)

        if delete_after:
            try:
                os.remove(file_path)
                print(f"🗑️ Deleted {file_path}")
            except Exception as e:
                print(f"⚠️ Could not delete {file_path}: {e}")

    if not all_doctors:
        print("⚠️ No providers extracted.")
        return []

    return all_doctors


# -----------------------------
# 5. Integrate into workflow
# -----------------------------
async def find_bcbs_providers(state: GraphState):
    insurance = state.get("insurance", "").lower()
    if "blue" not in insurance:
        print("⚠️ Currently supports only Blue Cross Blue Shield.")
        return state

    prefix = "ZGP"  # could be looked up dynamically later
    print(f"🔎 Searching BCBS with prefix {prefix} ...")

    await get_bcbs_html_multi(
        postal_code=state["postal_code"],
        prefix=prefix,
        specialty=state["specialty"],
        location=state["location"],
        max_pages=1,
        headless=True,
    )

    providers = parse_all_bcbs_pages(delete_after=True)
    state["providers"] = providers
    return state


# -----------------------------
# 6. Build LangGraph
# -----------------------------
graph = StateGraph(GraphState)
graph.add_node("GetUserInfo", get_user_info)
graph.add_node("FindBCBSProviders", find_bcbs_providers)

graph.add_edge(START, "GetUserInfo")
graph.add_edge("GetUserInfo", "FindBCBSProviders")
graph.add_edge("FindBCBSProviders", END)

app = graph.compile()


# -----------------------------
# 7. Run the workflow
# -----------------------------
async def run():
    result = await app.ainvoke({})
    print("\n=== FINAL OUTPUT ===")
    print(f"Extracted {len(result.get('providers', []))} providers.")
    if result["providers"]:
        for p in result["providers"][:5]:
            print(f"- {p['Name']} | {p['Specialty']} | {p['Address']} | {p['Phone']}")


if __name__ == "__main__":
    asyncio.run(run())
