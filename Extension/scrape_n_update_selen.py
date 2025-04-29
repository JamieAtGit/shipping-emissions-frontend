from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import random
import time

# === CONFIG ===
chrome_options = Options()
chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_options.add_argument("--headless")  # Optional: Run headless
chrome_options.add_argument("--log-level=3")  # Silence logs

# === UTILS ===
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

# === SCRAPER ===
def scrape_amazon_titles(url, max_items=5):
    driver = webdriver.Chrome(
        service=Service(r"C:\Drivers\chromedriver\chromedriver.exe"),
        options=chrome_options
    )
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "s-title-instructions-style"))
    )

    time.sleep(2)
    product_elements = driver.find_elements(By.CLASS_NAME, "s-title-instructions-style")
    print(f"🔍 Found {len(product_elements)} items")

    products = []
    for product in product_elements[:max_items]:
        try:
            title = product.text.strip()
            print("🛒", title)

            origin_country = estimate_origin_country(title)
            origin = origin_hubs[origin_country]
            distance = round(haversine(origin["lat"], origin["lon"], uk_hub["lat"], uk_hub["lon"]), 1)

            products.append({
                "title": title,
                "brand_estimated_origin": origin_country,
                "origin_city": origin["city"],
                "distance_origin_to_uk": distance,
                "distance_uk_to_user": 100,
                "estimated_weight_kg": round(random.uniform(0.5, 5.0), 2),
                "co2_emissions": None,
                "recyclability": random.choice(["Low", "Medium", "High"])
            })

        except Exception as e:
            print("⚠️ Error:", e)

    driver.quit()
    return products

# === SAVE ===
def save_products_to_json(products, path="data.json"):
    with open(path, "w") as f:
        json.dump(products, f, indent=2)
    print(f"✅ Saved {len(products)} product(s) to {path}")

# === MAIN ===
if __name__ == "__main__":
    urls = [
        "https://www.amazon.co.uk/s?k=usb+c+charger",
        "https://www.amazon.co.uk/s?k=laptop+stand"
    ]

    all_data = []
    for url in urls:
        all_data.extend(scrape_amazon_titles(url))

    save_products_to_json(all_data, "../ReactPopup/public/data.json")  # ⬅️ SAVE TO CORRECT LOCATION
