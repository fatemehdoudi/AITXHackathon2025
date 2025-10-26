import os
import googlemaps
from dotenv import load_dotenv
load_dotenv()
def clean_bcbs_address(raw_address: str) -> str:
    """Cleans and formats the raw address string from BCBS HTML."""
    clean_address = raw_address.split("•")[0].strip()
    return clean_address

def geocode_address(address: str):
    """Geocodes an address string into latitude and longitude using Google Maps API."""
    api_key = os.getenv("GOOGLE_GEOCODE_API_KEY")
    print('here is the google geocode api_key', api_key)
    gmaps = googlemaps.Client(key=api_key)
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            return None, None
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
        return None, None
