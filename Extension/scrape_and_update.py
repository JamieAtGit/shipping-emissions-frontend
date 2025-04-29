import requests
from bs4 import BeautifulSoup
import json
import random

def estimate_origin_country(title):
    title = title.lower()
    if "huawei" in title:
        return "China"
    elif "adidas" in title:
        return "Germany"
    elif "apple" in title:
        return "USA"
    elif "sony" in title:
        return "Japan"
    elif "dyson" in title:
        return "UK"
    return "China"

origin_hubs = {
    "China": {"lat": 31.2304, "lon": 121.4737, "city": "Shanghai"},
    "Germany": {"lat": 50.1109, "lon": 8.6821, "city": "Frankfurt"},
    "USA": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco"},
    "Japan": {"lat": 35.6895, "lon": 139.6917, "city": "Tokyo"},
    "UK": {"lat": 51.509865, "lon": -0.118092, "city": "London"}
}

uk_hub = {"lat": 51.8821, "lon": -0.5057, "city": "Dunstable"}

def haversine(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def scrape_product_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
    }
    response = requests.get(url, headers=headers)
    
    # 🧪 Check for CAPTCHA block
    if "captcha" in response.text.lower():
        print("🚫 CAPTCHA detected. Amazon blocked the request.")
        print(response.text[:1000])  # Still show the content
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Try fallback selectors for robustness
    title_elem = (
        soup.find("span", id="productTitle") or
        soup.select_one("h1 span") or
        soup.select_one("title")
    )

    print(response.text[:1000])  # 👈 Preview the raw HTML

    if not title_elem:
        print("❌ Couldn't find title.")
        return []

    title = title_elem.text.strip()
    print("✅ Title:", title)

    origin_country = estimate_origin_country(title)
    origin = origin_hubs[origin_country]

    intl_distance = round(haversine(origin["lat"], origin["lon"], uk_hub["lat"], uk_hub["lon"]), 1)

    product = {
        "title": title,
        "brand_estimated_origin": origin_country,
        "origin_city": origin["city"],
        "distance_origin_to_uk": intl_distance,
        "distance_uk_to_user": 100,  # Placeholder
        "estimated_weight_kg": round(random.uniform(0.5, 5.0), 2),
        "co2_emissions": None,
        "recyclability": random.choice(["Low", "Medium", "High"])
    }

    return [product]


def save_to_file(data, filename="data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    url = "https://www.amazon.co.uk/dp/B0C2L7T4DN"
    results = scrape_product_page(url)
    save_to_file(results)
    print(f"✅ Scraped and saved {len(results)} product(s).")
