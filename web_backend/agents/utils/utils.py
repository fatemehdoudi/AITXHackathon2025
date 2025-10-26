import json, re
import asyncio, os, csv, re, glob, hashlib, json, requests
from typing import TypedDict, Optional

def city_state_from_zip(zip_code: str):
    """Return (city, state_abbr) for a US 5-digit ZIP, else (None, None)."""
    zip_code = (zip_code or "").strip()
    if not re.fullmatch(r"\d{5}", zip_code):
        return None, None
    try:
        r = requests.get(f"https://api.zippopotam.us/us/{zip_code}", timeout=8)
        if r.status_code != 200:
            return None, None
        data = r.json()
        places = data.get("places") or []
        if not places:
            return None, None
        city = places[0].get("place name")
        state_abbr = places[0].get("state abbreviation")
        if city and state_abbr:
            return city, state_abbr
    except Exception:
        pass
    return None, None


def cleanup_temp_data():
    if os.path.exists("doctor_pages"):
        for f in glob.glob("doctor_pages/*.html"):
            try:
                os.remove(f)
            except:
                pass
        try:
            os.rmdir("doctor_pages")
        except:
            pass


