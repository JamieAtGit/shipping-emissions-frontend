# As a temporary workaround, try this at the top of the file
import sys
print(sys.executable)
import csv
import os
import json
import random
import re
import time
from datetime import datetime



import traceback
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

fallback_mode = False


# === Load custom brand location metadata ===

class Log:
    @staticmethod
    def info(msg): print(f"\033[94mℹ️ {msg}\033[0m")
    @staticmethod
    def success(msg): print(f"\033[92m✅ {msg}\033[0m")
    @staticmethod
    def warn(msg): print(f"\033[93m⚠️ {msg}\033[0m")
    @staticmethod
    def error(msg): print(f"\033[91m❌ {msg}\033[0m")

def safe_get(driver, url, retries=3, wait=10):
    for i in range(retries):
        try:
            if not safe_get(driver, url):
                Log.error(f"🛑 Giving up on URL: {url}")
                return []  # Or return None / skip product depending on context


            # Check for common Amazon anti-bot pages
            page_source = driver.page_source.lower()
            if "service unavailable" in page_source or "robot check" in page_source or "we're sorry" in page_source:
                Log.warn(f"🚫 Blocked or 503 at {url}. Retrying ({i+1}/{retries})...")
                time.sleep(wait * (i+1))
                continue

            return True  # success
        except Exception as e:
            Log.warn(f"❌ Failed to load {url} (attempt {i+1}): {e}")
            time.sleep(wait * (i+1))
    return False


# === PRIORITY PRODUCTS DB ===
priority_products = {}
try:
    with open("priority_products.json", "r", encoding="utf-8") as f:
        priority_products = json.load(f)
    Log.success(f"✅ Loaded {len(priority_products)} high-accuracy products.")
except FileNotFoundError:
    Log.warn("priority_products.json not found. Starting with empty product DB.")
except Exception as e:
    Log.error(f"Error loading priority product DB: {e}")


brand_locations = {}
try:
    with open("brand_locations.json", "r", encoding="utf-8") as f:
        brand_locations = json.load(f)
    Log.success(f"📦 Loaded {len(brand_locations)} custom brand locations.")
except Exception as e:
    Log.warn(f" Could not load brand_locations.json: {e}")


# === CONFIG ===
ua = UserAgent()
chrome_options = Options()
chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_options.add_argument("--headless")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("window-size=1280,800")  # 🖥️ Simulate realistic screen
chrome_options.add_argument("--lang=en-GB")  # Optional: browser language


# 🧢 Rotate user-agent for stealth
random_user_agent = ua.random
chrome_options.add_argument(f"user-agent={random_user_agent}")
Log.info(f"🧢 Using User-Agent: {random_user_agent}")



# === Load external brand origins CSV ===
brand_origin_lookup = {}
try:
    with open("brand_origins.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            brand = row["brand"].lower()
            brand_origin_lookup[brand] = {
                "country": row["hq_country"],
                "city": row["hq_city"]
            }
except FileNotFoundError:
    Log.warn("brand_origins.csv not found. Defaulting to heuristic mapping.")


origin_hubs = {
    "China": {"lat": 31.2304, "lon": 121.4737, "city": "Shanghai"},
    "Germany": {"lat": 50.1109, "lon": 8.6821, "city": "Frankfurt"},
    "USA": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco"},
    "Japan": {"lat": 35.6895, "lon": 139.6917, "city": "Tokyo"},
    "UK": {"lat": 51.509865, "lon": -0.118092, "city": "London"},
    "Italy": {"city": "Castel San Giovanni", "lat": 45.0667, "lon": 9.4167},
    "India": {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi"},
    "South Korea": {"lat": 37.5665, "lon": 126.9780, "city": "Seoul"},
    "Spain": {"lat": 40.4168, "lon": -3.7038, "city": "Madrid"},
    "Poland": {"lat": 52.2297, "lon": 21.0122, "city": "Warsaw"},
    "Netherlands": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam"},
}
uk_hub = {"lat": 51.8821, "lon": -0.5057, "city": "Dunstable"}

known_brand_origins = {
    "huel": "UK",
    "avm": "Germany",
    "anker": "China",
    "bosch": "Germany",
    "philips": "Netherlands",
    "sony": "Japan",
    "samsung": "South Korea",
    "apple": "USA",
    "lenovo": "China",
    "asus": "Taiwan",
    "fender": "USA",
    "kinetica": "Ireland",
    "xiaomi": "China",
    "dyson": "UK",
    "adidas": "Germany",
    "nokia": "Finland",
    "logitech": "Switzerland",
    "tcl": "China",
    "tefal": "France",
    "panasonic": "Japan",
    "microsoft": "USA",
    "nintendo": "Japan",

}


amazon_fulfillment_centers = {
    "UK": {"lat": 51.8821, "lon": -0.5057, "city": "Dunstable"},
    "Germany": {"lat": 50.1109, "lon": 8.6821, "city": "Frankfurt"},
    "France": {"lat": 48.8566, "lon": 2.3522, "city": "Paris"},
    "Italy": {"lat": 45.0667, "lon": 9.4167, "city": "Castel San Giovanni"},
    "USA": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco"},
    "Spain": {"lat": 40.4168, "lon": -3.7038, "city": "Madrid"},
    "Netherlands": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam"},
    "Poland": {"lat": 52.2297, "lon": 21.0122, "city": "Warsaw"},
}


def fuzzy_normalize_origin(raw_origin):
    if not raw_origin:
        return "Unknown"

    origin = raw_origin.strip().lower()

    # Keyword-based fuzzy mapping
    fuzzy_map = {
        "uk": ["united kingdom", "uk", "england", "scotland", "wales"],
        "usa": ["united states", "united states of america", "us", "usa"],
        "china": ["china", "prc"],
        "germany": ["germany"],
        "france": ["france"],
        "italy": ["italy"],
        "japan": ["japan"],
        "ireland": ["ireland", "eire"],
        "netherlands": ["netherlands", "holland"],
        "canada": ["canada"],
        "switzerland": ["switzerland"],
        "australia": ["australia"],
        "sweden": ["sweden"],
        "finland": ["finland"],
        "mexico": ["mexico"],
    }

    for country, keywords in fuzzy_map.items():
        if any(keyword in origin for keyword in keywords):
            return country.title()

    return raw_origin.title()


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

def extract_shipping_origin(driver):
    try:
        candidates = driver.find_elements(By.XPATH, "//div[contains(text(), 'Ships from') or contains(text(), 'Sold by') or contains(text(),'Dispatches from')]")
        for el in candidates:
            text = el.text.lower()
            if "china" in text:
                return "China"
            elif "germany" in text:
                return "Germany"
            elif "united states" in text or "usa" in text:
                return "USA"
            elif "uk" in text or "united kingdom" in text:
                return "UK"
            elif "italy" in text:
                return "Italy"
            elif "france" in text:
                return "France"
    except Exception as e:
        Log.warn(f"⚠️ Could not extract shipping origin: {e}")
    return None


def is_high_confidence(product):
    return (
        product.get("brand_estimated_origin") not in ["Unknown", None] and
        isinstance(product.get("estimated_weight_kg"), (int, float)) and
        product.get("dimensions_cm") not in [None, ""] and
        product.get("asin") is not None
    )

def maybe_add_to_priority(product, priority_db, save_path="priority_products.json"):
    asin = product.get("asin")
    if not asin or asin in priority_db:
        return False

    if is_high_confidence(product):
        product["confidence"] = "High"
        priority_db[asin] = product

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(priority_db, f, indent=2)
        
        Log.success(f"🔐 Added {asin} to priority_products.json")
        return True
    
    return False



def extract_asin(url):
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not match:
        match = re.search(r"/gp/product/([A-Z0-9]{10})", url)
    if not match:
        match = re.search(r"/product/([A-Z0-9]{10})", url)
    if not match:
        match = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", url)
    return match.group(1) if match else None


def extract_weight(text):
    if not text:
        return None

    text = text.lower()

    # 1. Match kg first (also handles "kilogram" or "kilograms")
    kg_match = re.search(r"([\d.]+)\s?(kg|kilogram|kilograms)", text)
    if kg_match:
        return round(float(kg_match.group(1)), 3)

    # 2. Match grams
    g_match = re.search(r"([\d.]+)\s?g", text)
    if g_match:
        return round(float(g_match.group(1)) / 1000, 3)

    return None




def extract_dimensions(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s?[x×*]\s?(\d+(?:\.\d+)?)\s?[x×*]\s?(\d+(?:\.\d+)?)(?:\s?cm|centimeters?)", text)
    if match:
        return f"{match.group(1)} x {match.group(2)} x {match.group(3)} cm"
    return None


def extract_material(text):
    match = re.search(r"(?:material|made of|composition)[\s:]+([a-z\s\-]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    return None







def haversine(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def is_invalid_brand(candidate):
    candidate = candidate.lower()
    return (
        candidate in ["usb", "type", "plug", "cable", "portable", "wireless", "eco", "fast", "unknown"]
        or re.match(r"^\d+[a-z]{0,3}$", candidate)  # e.g., 65w, 100w
        or candidate.isdigit()
    )


def resolve_brand_origin(brand_key, title_fallback=None):
    global brand_locations

    # Normalize brand key
    brand_key = brand_key.lower().strip()
    
    # 0. Force known_brand_origins if available
    if brand_key in known_brand_origins:
        country = known_brand_origins[brand_key]
        city = origin_hubs.get(country, origin_hubs["UK"])["city"]
        return country, city


    # 1. Direct match in enriched brand_locations
    if brand_key in brand_locations:
        return brand_locations[brand_key]["origin"]["country"], brand_locations[brand_key]["origin"]["city"]

    # 2. Match in brand_origin_lookup CSV
    elif brand_key in brand_origin_lookup:
        return brand_origin_lookup[brand_key]["country"], brand_origin_lookup[brand_key]["city"]

    # 3. Match in hardcoded known_brand_origins
    elif brand_key in known_brand_origins:
        country = known_brand_origins[brand_key]
        city = origin_hubs.get(country, origin_hubs["UK"])["city"]
        return country, city

    # 4. Fallback — guess using product title, and save to brand_locations
    else:
        Log.warn(f"⚠️ Unrecognized brand: {brand_key}")
        if title_fallback:
            guessed_country = estimate_origin_country(title_fallback)
            guessed_city = origin_hubs.get(guessed_country, origin_hubs["UK"])["city"]
            brand_locations[brand_key] = {
                "origin": {
                    "country": guessed_country,
                    "city": guessed_city
                },
                "fulfillment": "UK"
            }
            save_brand_locations()
            Log.success(f"📦 Learned origin from title: {brand_key} → {guessed_country}")
            return guessed_country, guessed_city

        # 5. Log unknown brand
        # Ensure unrecognized_brands.txt exists
        if not os.path.exists("unrecognized_brands.txt"):
            with open("unrecognized_brands.txt", "w", encoding="utf-8") as f:
                f.write("")  # create an empty file

        with open("unrecognized_brands.txt", "a", encoding="utf-8") as log:
            log.write(f"{brand_key}\n")
        return "Unknown", "Unknown"
    




def infer_fulfillment_country(url, sold_by_text=""):
    url = url.lower()
    sold_by_text = sold_by_text.lower()
    if "amazon.co.uk" in url or "dispatched from and sold by amazon" in sold_by_text:
        return "UK"
    elif "amazon.de" in url or "versand durch amazon" in sold_by_text:
        return "Germany"
    elif "amazon.fr" in url:
        return "France"
    elif "amazon.it" in url:
        return "Italy"
    elif "amazon.com" in url:
        return "USA"
    return "UK"  # fallback default

def save_brand_locations():
    global brand_locations
    with open("brand_locations.json", "w", encoding="utf-8") as f:
        json.dump(brand_locations, f, indent=2)
        Log.success(f"📦 Saved updated brand_locations.json with {len(brand_locations)} entries.")

def safe_save_brand_origin(brand_key, country, city="Unknown"):
    if not country or country.lower() == "unknown":
        return  # Skip invalid

    current = brand_locations.get(brand_key, {}).get("origin", {})
    current_country = current.get("country", "").lower()

    if current_country != country.lower():
        brand_locations[brand_key] = {
            "origin": {
                "country": country,
                "city": city
            },
            "fulfillment": "UK"
        }
        save_brand_locations()
        Log.success(f"📦 Inferred and saved origin for {brand_key}: {country}")


def enrich_brand_location(brand_name, example_url):
    global brand_locations

    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(example_url)

    try:
        text_blobs = []
        legacy_specs = []

        # Try pulling merchant info or description
        try:
            merchant = driver.find_element(By.ID, "merchant-info").text
            text_blobs.append(merchant)
        except:
            pass

        try:
            desc = driver.find_element(By.ID, "productDescription").text
            text_blobs.append(desc)
        except:
            pass

        try:
            bullets = driver.find_elements(By.CSS_SELECTOR, "#feature-bullets li")
            text_blobs += [b.text for b in bullets]
        except:
            pass

        for blob in text_blobs:
            blob = blob.lower()
            if "made in" in blob or "manufactured in" in blob:
                match = re.search(r"(made|manufactured)\s+in\s+([a-z\s,]+)", blob)
                if match:
                    location = match.group(2).strip().title()
                    country = location.split(",")[-1].strip()
                    city = location.split(",")[0].strip() if "," in location else "Unknown"

                    print(f"🔍 Guessed: {brand_name} → {city}, {country}")

                    brand_locations[brand_name] = {
                        "origin": {
                            "country": country,
                            "city": city
                        },
                        "fulfillment": "UK"
                    }
                     # 🚀 Save it instantly
                    save_brand_locations()
                    return

        print(f"❌ No location found for: {brand_name}")

    finally:
        driver.quit()

# Example enrichment script
# Ensure the unrecognized_brands.txt file exists before reading
if not os.path.exists("unrecognized_brands.txt"):
    with open("unrecognized_brands.txt", "w", encoding="utf-8") as f:
        f.write("")  # just creates the file if it doesn't exist

with open("unrecognized_brands.txt", "r", encoding="utf-8") as f:
    brands_to_enrich = set(line.strip() for line in f if line.strip())

# Dummy mapping — replace with real example URLs per brand
example_urls = {
    "anker": "https://www.amazon.co.uk/dp/B09KT1NR6V",
    "huel": "https://www.amazon.co.uk/dp/B0CFQKQNX3",
    "avm": "https://www.amazon.co.uk/dp/B01N8S4URO"
}

def finalize_product_entry(product):
    """
    Ensures product has all required fields: origin, city, weight.
    Enriches brand origin if missing. Updates all product DBs.
    """
    brand_key = product.get("brand", product.get("title", "").split()[0]).lower().strip()
    title = product.get("title", "")
    
    # Resolve missing origin
    if not product.get("brand_estimated_origin") or product["brand_estimated_origin"].lower() in ["unknown", "other", ""]:
        country, city = resolve_brand_origin(brand_key, title)
        product["brand_estimated_origin"] = country
        product["origin_city"] = city

    # Resolve missing weight
    if not product.get("estimated_weight_kg"):
        fallback_weight = extract_weight(title)
        if fallback_weight:
            product["estimated_weight_kg"] = fallback_weight
            Log.warn(f"⚖️ Fallback weight from title: {fallback_weight} kg")

    # Save to cleaned products
    try:
        cleaned_path = "cleaned_products.json"
        if os.path.exists(cleaned_path):
            with open(cleaned_path, "r", encoding="utf-8") as f:
                cleaned = json.load(f)
        else:
            cleaned = []

        cleaned.append(product)
        with open(cleaned_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)
        Log.success("🧽 Product added to cleaned_products.json")
    except Exception as e:
        Log.warn(f"⚠️ Could not write to cleaned_products.json: {e}")

    # Save to priority products if high quality
    maybe_add_to_priority(product, priority_products)


for brand in brands_to_enrich:
    if brand in example_urls:
        enrich_brand_location(brand, example_urls[brand])

# ✅ Save to JSON here, after loop is complete
with open("brand_locations.json", "w", encoding="utf-8") as f:
    json.dump(brand_locations, f, indent=2)
    Log.success(f"📦 Saved updated brand_locations.json with {len(brand_locations)} entries.")


def extract_recyclability(text_blobs):
    full_text = " ".join(text_blobs).lower()
    if any(kw in full_text for kw in ["100% recyclable", "fully recyclable", "recyclable packaging"]):
        return "High"
    elif any(kw in full_text for kw in ["partially recycled", "made from recycled", "recycled content"]):
        return "Medium"
    elif any(kw in full_text for kw in ["not recyclable", "non-recyclable", "plastic packaging"]):
        return "Low"
    return "Unknown"



# === SCRAPER for search result pages ===
def scrape_amazon_titles(url, max_items=100):

    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    global brand_locations # potential bug fix
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    # Optional: reuse your chrome_options if needed
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Optional: run without headless so you can see it (or set headless if you want stealth mode)
    # options.headless = True


    if not safe_get(driver, url):
        Log.error(f"🛑 Giving up on URL: {url}")
        return []  # Or return None / skip product depending on context


    try:
        print("📍 Waiting for product title...")

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.s-main-slot div[data-asin]"))
        )
    except:
        print("❌ Could not find product containers.")
        driver.quit()
        return []

    time.sleep(2)

    product_elements = driver.find_elements(By.CSS_SELECTOR, "div.s-main-slot div[data-asin]")
    print(f"🔍 Found {len(product_elements)} items")

    products = []
    for product in product_elements:
        if len(products) >= max_items:
            break

        try:
            asin = product.get_attribute("data-asin")
            if not asin:
                continue

            link_el = product.find_element(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")
            href = link_el.get_attribute("href")

            title = None
            title_selectors = [
                "span.a-size-medium.a-color-base.a-text-normal",
                "span.a-size-base-plus.a-color-base.a-text-normal",
                "h2 span"
            ]
            
            for selector in title_selectors:
                try:
                    title_el = product.find_element(By.CSS_SELECTOR, selector)
                    title = title_el.text.strip()
                    if title:
                        break
                except:
                    continue

            if not title:
                print("❌ Skipping: Could not find product title")
                continue
            


            
            # === BRAND DETECTION ===
            brand = None

            # 1. Try data-brand
            brand_attr = product.get_attribute("data-brand")
            if brand_attr and len(brand_attr.strip()) > 1:
                brand = brand_attr.strip()

            # 2. Try known selectors
            if not brand:
                try:
                    el = product.find_element(By.CSS_SELECTOR, "h5.s-line-clamp-1 span.a-size-base")
                    brand = el.text.strip()
                except:
                    pass
            #2.5. trying aria-label attributes
            aria_label = product.get_attribute("aria-label")
            if aria_label:
                for known_brand in list(known_brand_origins.keys()) + list(brand_origin_lookup.keys()):
                    if known_brand in aria_label.lower():
                        brand = known_brand.capitalize()
                        Log.info(f"🔍 Inferred brand from aria-label: {brand}")
                        break

            # 3. Try scanning title for known brands
            if not brand:
                for known_brand in list(known_brand_origins.keys()) + list(brand_origin_lookup.keys()):
                    if known_brand in title.lower():
                        brand = known_brand.capitalize()
                        break
                    
            #3.5. Full product block text scrape (last proper resort)      
            if not brand:
                full_text = product.text.lower()
                for known_brand in list(known_brand_origins.keys()) + list(brand_origin_lookup.keys()):
                    if known_brand in full_text:
                        brand = known_brand.capitalize()
                        Log.info(f"🧾 Matched brand from full block text: {brand}")
                        break


            # 4. Fallback to first word
            if not brand:
                fallback = title.split()[0].lower()
                if fallback in ["usb", "wireless", "portable", "led", "plug", "type", "eco", "bottle"] or re.match(r"^\d+[a-z]{0,2}$", fallback):
                    brand = "Unknown"
                else:
                    brand = fallback.capitalize()

            # Final guard
            if brand.lower() == "unknown":
                Log.warn(f"⚠️ Captured unknown brand from title: {title}")
                # Ensure the file exists
                if not os.path.exists("unrecognized_brands.txt"):
                    with open("unrecognized_brands.txt", "w", encoding="utf-8") as f:
                        f.write("")  # create an empty file

                with open("unrecognized_brands.txt", "a", encoding="utf-8") as log:
                    log.write(f"{brand_key}\n")




            print("🛒", title)
            
            brand_key = brand.lower().strip()
            # Try to enrich brand location if unknown
            if brand_key not in brand_locations:
                enrich_brand_location(brand_key, href)  # call live scraper
                # Reload JSON after enrichment
                try:
                    with open("brand_locations.json", "r", encoding="utf-8") as f:
                        brand_locations = json.load(f)
                    Log.success(f"📦 Updated brand_locations.json after enriching {brand_key}")
                except Exception as e:
                    Log.warn(f"⚠️ Failed to reload brand_locations after enriching {brand_key}: {e}")

            # Use resolved location
            origin_country, origin_city = resolve_brand_origin(brand_key)

                  
            origin = origin_hubs.get(origin_country, origin_hubs["UK"])
            fulfillment_country = infer_fulfillment_country(href)  # or use `url` in the product page
            fulfillment_hub = amazon_fulfillment_centers.get(fulfillment_country, amazon_fulfillment_centers["UK"])
            distance = round(haversine(origin["lat"], origin["lon"], fulfillment_hub["lat"], fulfillment_hub["lon"]), 1)


            weight = None
            try:
                # Try scraping tech specs first
                tech_details = driver.find_elements(By.CSS_SELECTOR, "#prodDetails td")
                for i in range(len(tech_details) - 1):
                    label = tech_details[i].text.lower()
                    value = tech_details[i + 1].text.lower()
                    if "weight" in label:
                        weight = extract_weight(value)
                        print(f"⚖️ Extracted from tech spec: {weight} kg")
                        break

                # Only fallback after the loop
                if not weight:
                    extracted_weight = extract_weight(title)
                    if extracted_weight:
                        weight = extracted_weight
                        print(f"⚠️ Fallback used — extracted from title: {weight} kg")

                       
            except:
                pass

            if not origin_country or origin_country.lower() in ["unknown", "other", ""]:
                origin_country, origin_city = resolve_brand_origin(brand_key, title)

            if not weight:
                weight = extract_weight(title)
                        

            products.append({
                "asin": asin,
                "title": title,
                "brand_estimated_origin": origin_country,
                "origin_city": origin_city,
                "distance_origin_to_uk": distance,
                "distance_uk_to_user": 100,
                "estimated_weight_kg": weight,
                "co2_emissions": None,
                "recyclability": random.choice(["Low", "Medium", "High"])
            })

        except Exception as e:
            print("⚠️ Skipping product due to error:", e)

        # Save to cleaned_products.json
        try:
            cleaned_path = "cleaned_products.json"
            if os.path.exists(cleaned_path):
                with open(cleaned_path, "r", encoding="utf-8") as f:
                    cleaned = json.load(f)
            else:
                cleaned = []

            cleaned.append(product)
            with open(cleaned_path, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=2)
            Log.success("🧽 Product added to cleaned_products.json")
            
            
        except Exception as e:
            Log.warn(f"⚠️ Could not write to cleaned_products.json: {e}")

    driver.quit()
    return products


import os

IS_DOCKER = os.environ.get('IS_DOCKER', 'false').lower() == 'true'

def scrape_amazon_product_page(amazon_url, fallback=False):
    if IS_DOCKER:
        fallback = True
        
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    print("🧪 Inside scraper function, fallback mode is:", fallback)

    if fallback:
        print("🟡 Using fallback mode, returning mock product.")
        return {
            "title": "Test Product (Fallback Mode)",
            "origin": "Unknown",
            "weight_kg": 0.6,
            "dimensions_cm": [20, 10, 5],
            "material_type": "Plastic",
            "recyclability": "Low",
            "eco_score_ml": "F",
            "transport_mode": "Land",
            "carbon_kg": None
        }

    driver = None
    
    
    
    try:
        print("🚀 Launching undetected ChromeDriver...")
        from undetected_chromedriver import Chrome, ChromeOptions
        options = ChromeOptions()
        options.user_data_dir = "selenium_profile"  # Folder to store persistent session/cookies
        driver = Chrome(headless=False, options=options)


        print("🌐 Navigating to page:", amazon_url)
        driver.get(amazon_url)
        driver.implicitly_wait(5)
        
        text_blobs = [] 
        legacy_specs = [] 
        
        
 # === 🛡️ Bot detection handling ===
        page = driver.page_source.lower()
        if "robot check" in page or "captcha" in page:
            print("🛑 CAPTCHA detected! Saving screenshot...")

            driver.save_screenshot("captcha_screenshot.png")
            print("📸 Saved screenshot as captcha_screenshot.png")
            print("🧍 Please solve the CAPTCHA in the Chrome window.")
            input("✅ Press Enter here once you've solved the CAPTCHA and see the product page...")

            print("🔁 Retrying scrape after CAPTCHA solve...")

            # Re-fetch page content after manual solve
            page = driver.page_source.lower()
            if "robot check" in page or "captcha" in page:
                print("❌ CAPTCHA still present after retry. Giving up.")
                return None


        # Bot detection check
        page = driver.page_source.lower()
        if "robot check" in page or "captcha" in page:
            print("🛑 Blocked by CAPTCHA / bot check.")
            return None

        print("🖱️ Simulating scroll + click...")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
            time.sleep(random.uniform(1, 2))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
            time.sleep(random.uniform(1.5, 2.5))
        except Exception as e:
            print(f"⚠️ Scroll simulation failed: {e}")

        # Try to expand spec blocks
        try:
            expandable = driver.find_elements(By.CSS_SELECTOR, ".a-expander-header")
            if expandable:
                random.choice(expandable).click()
                time.sleep(random.uniform(1, 2))
        except:
            pass

        # Hover over title
        try:
            hover_target = driver.find_element(By.ID, "productTitle")
            webdriver.ActionChains(driver).move_to_element(hover_target).perform()
            time.sleep(random.uniform(0.5, 1.2))
        except:
            pass

        # Wait and parse title
        title = None
        selectors = [
            (By.ID, "productTitle"),
            (By.CSS_SELECTOR, "#title span"),
            (By.CSS_SELECTOR, "span#productTitle"),
            (By.CSS_SELECTOR, "h1.a-size-large span")
        ]
        for by, selector in selectors:
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((by, selector)))
                title = driver.find_element(by, selector).text.strip()
                break
            except:
                continue

        if not title:
            print(f"❌ Failed to extract product title for: {amazon_url}")
            return None

        asin = extract_asin(amazon_url)
        if asin in priority_products:
            Log.success("🎯 Using locked metadata for high-accuracy product.")
            return priority_products[asin]

        try:
            brand = driver.find_element(By.ID, "bylineInfo").text.strip()
        except:
            brand = title.split()[0]

        def normalize_brand(brand_raw):
            return brand_raw.lower().replace("visit the", "").replace("store", "").strip()

        # Use it like this:
        brand_name = normalize_brand(brand)
        brand_key = brand_name  # already normalized

        print("🧾 Raw brand text:", brand_name)


        if brand_key not in brand_origin_lookup and brand_key not in known_brand_origins:
            # Ensure the file exists
            if not os.path.exists("unrecognized_brands.txt"):
                with open("unrecognized_brands.txt", "w", encoding="utf-8") as f:
                    f.write("")  # create an empty file

            with open("unrecognized_brands.txt", "a", encoding="utf-8") as log:
                log.write(f"{brand_name}\n")

        if brand_key not in brand_locations:
            enrich_brand_location(brand_name, amazon_url)

        # === ORIGIN PRIORITY: page blob > brand DB > title fallback > shipping
        origin_country = "Unknown"
        origin_city = "Unknown"
        origin_source = "Unknown"


        # ✅ Only run fallback origin logic if still unknown
        if origin_country in ["Unknown", "Other", None, ""]:

            # 1. Try to extract origin from page blobs
            for blob in text_blobs:
                legacy_specs = []
                if any(kw in blob for kw in ["country of origin", "made in", "manufacturer"]):
                    match = re.search(r"(?:origin[:\s]*|made in[:\s]*|manufacturer(?:ed)? in[:\s]*)([a-zA-Z\s,]+)", blob)
                    if match:
                        raw_origin = match.group(1).strip()
                        if raw_origin.lower() not in ["no", "not specified", "unknown"]:
                            origin_country = fuzzy_normalize_origin(raw_origin)
                            origin_city = origin_hubs.get(origin_country, {}).get("city", "Unknown")
                            origin_source = "blob_match"
                            print(f"📍 Extracted origin from blob: {raw_origin} → {origin_country}")
                            break

            # 1.5 Check legacy tech specs
            if origin_country in ["Unknown", "Other", None, ""]:
                try:
                    for i in range(len(legacy_specs) - 1):
                        label = legacy_specs[i].text.lower().strip()
                        value = legacy_specs[i + 1].text.strip()
                        if "country of origin" in label:
                            origin_country = fuzzy_normalize_origin(value)
                            origin_city = origin_hubs.get(origin_country, {}).get("city", "Unknown")
                            origin_source = "techspec_origin"
                            print(f"📍 Found origin in tech spec: {value} → {origin_country}")
                            break
                except Exception as e:
                    Log.warn(f"⚠️ Error checking tech spec for origin: {e}")

            # 2. Fallback: brand DB, but only if page didn’t already give a specific origin
            if origin_country in ["Unknown", "Other", None, ""]:
                db_origin_country, db_origin_city = resolve_brand_origin(brand_key, title)
                origin_country = db_origin_country
                origin_city = db_origin_city
                origin_source = "brand_db"
            else:
                print(f"🛡️ Preserving explicit product origin: {origin_country} (source: {origin_source})")

            # 3. Fallback: title guess
            if origin_country in ["Unknown", "Other", None, ""] and origin_source not in ["brand_db", "blob_match", "techspec_origin"]:
                origin_city = origin_hubs.get(origin_country, {}).get("city", "Unknown")
                origin_source = "title_guess"
                print(f"🧠 Fallback origin estimate from title: {guess}")
            else:
                print(f"🚫 Skipping fallback origin guess — origin already resolved from {origin_source}")


            # 4. Final fallback: shipping panel
            if origin_country in ["Unknown", "Other", None, ""]:
                guess = extract_shipping_origin(driver)
                if guess:
                    origin_country = fuzzy_normalize_origin(guess)
                    origin_city = origin_hubs.get(origin_country, {}).get("city", "Unknown")
                    origin_source = "shipping_panel"
                    print(f"🚚 Inferred origin from shipping panel: {guess}")
                    
            # 🛡️ Final fallback override guard to protect brand DB origin
            if origin_source == "brand_db":
                origin_country = known_brand_origins.get(brand_key, origin_country)
                origin_city = origin_hubs.get(origin_country, {}).get("city", "Unknown")
                print(f"🛡️ Protected origin override — sticking with brand DB: {origin_country}")

            print(f"🎯 Returning final origin: {origin_country} (source: {origin_source})")

            # 🛡️ Final override protection
            if asin in priority_products:
                origin_country = priority_products[asin].get("brand_estimated_origin", origin_country)
                origin_city = priority_products[asin].get("origin_city", origin_city)
                print(f"🔒 Restored origin from priority DB: {origin_country}")

        else:
            print(f"🌍 Skipping all fallbacks — origin already set to: {origin_country} (source: {origin_source})")


        # Scrape materials, weight, dimensions
        weight = dimensions = material = recyclability = None
        try:
            text_blobs = []
            legacy_specs = []

            bullets = driver.find_elements(By.CSS_SELECTOR, "#detailBullets_feature_div li")
            kv_rows = driver.find_elements(By.CSS_SELECTOR, "table.a-keyvalue tr")
            desc = driver.find_elements(By.ID, "productDescription")

            # ✅ Safe default + attempt to assign if possible
            legacy_specs = []
            try:
                legacy_specs = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 td")
            except:
                pass

            # 📦 Now collect all into text_blobs
            text_blobs += [b.text.strip().lower() for b in bullets]
            text_blobs += [r.text.strip().lower() for r in kv_rows]
            text_blobs += [l.text.strip().lower() for l in legacy_specs]
            text_blobs += [d.text.strip().lower() for d in desc]

            print("🔍 Starting to parse text blobs for product details...")

            
            origin_already_saved = False  # ✅ Add this before the loop

            for blob in text_blobs:
                legacy_specs = []
                if not weight and any(kw in blob for kw in ["weight", "weighs", "item weight", "product weight"]):
                    extracted_weight = extract_weight(blob)
                    if extracted_weight:
                        weight = extracted_weight
                        print(f"⚖️ Extracted weight: {weight} kg")

                if not weight:
                    extracted_weight = extract_weight(title)
                    if extracted_weight:
                        weight = extracted_weight
                        print(f"⚠️ Extracted from title fallback: {weight} kg")

                if not dimensions:
                    extracted_dimensions = extract_dimensions(blob)
                    if extracted_dimensions:
                        dimensions = extracted_dimensions
                        print(f"📦 Extracted dimensions: {dimensions} cm")

                if not material:
                    extracted_material = extract_material(blob)
                    if extracted_material:
                        material = extracted_material
                        print(f"🧬 Extracted material: {material}")

                # ✅ Save brand origin only ONCE
                if not origin_already_saved:
                    safe_save_brand_origin(brand_key, origin_country, origin_city)
                    origin_already_saved = True

                if weight and dimensions and material and origin_country:
                    print("✅ All key details found.")
                    break
                
                
            recyclability = extract_recyclability(text_blobs)

        except Exception as e:
            print("⚠️ Extraction error:", e)

        if not weight:
            print("⚠️ Weight not found in specs, using fallback.")
            weight = 1.0  # Only fallback if nothing extracted at all

        # ✅ Only use shipping panel if origin is still unknown
        if origin_country in ["Unknown", "Other", None, ""]:
            guess = extract_shipping_origin(driver)
            if guess:
                origin_country = fuzzy_normalize_origin(guess)
                origin_city = origin_hubs.get(origin_country, {}).get("city", "Unknown")
                origin_source = "shipping_panel"
                print(f"🚚 Inferred origin from shipping panel: {guess}")
        else:
            print(f"🛡️ Protected origin: {origin_country} (source: {origin_source})")


        origin_hub = origin_hubs.get(origin_country, origin_hubs["UK"])
        distance = round(haversine(origin_hub["lat"], origin_hub["lon"], uk_hub["lat"], uk_hub["lon"]), 1)

            # === Infer smarter transport mode
        long_distance_countries = ["China", "USA", "Japan"]
        if origin_country in long_distance_countries:
            transport_mode = "Ship"
        elif origin_country == "UK":
            transport_mode = "Land"
        else:
            transport_mode = "Air"

        

        # === ✅ Fuzzy corrections for material and origin (place it HERE)
        if material:
            mat = material.lower()
            if "plastic" in mat:
                material = "Plastic"
            elif "glass" in mat:
                material = "Glass"
            elif "alum" in mat:
                material = "Aluminium"
            elif "steel" in mat:
                material = "Steel"
            elif "paper" in mat:
                material = "Paper"
            elif "cardboard" in mat:
                material = "Cardboard"

        if origin_country:
            orig = origin_country.lower()
            if "china" in orig:
                origin_country = "China"
            elif "united kingdom" in orig or "uk" in orig:
                origin_country = "UK"
            elif "usa" in orig or "united states" in orig:
                origin_country = "USA"
            elif "germany" in orig:
                origin_country = "Germany"
            elif "france" in orig:
                origin_country = "France"
            elif "italy" in orig:
                origin_country = "Italy"


        # 🔒 Final override if product is in trusted DB
        if asin in priority_products:
            trusted = priority_products[asin]
            origin_country = trusted.get("brand_estimated_origin", origin_country)
            origin_city = trusted.get("origin_city", origin_city)
            print(f"🔒 Final override from priority DB: {origin_country}")
            
        # Calculate distance here before assigning to product
        origin_hub = origin_hubs.get(origin_country, origin_hubs["UK"])
        distance_origin_to_uk = round(haversine(origin_hub["lat"], origin_hub["lon"], uk_hub["lat"], uk_hub["lon"]), 1)
        distance_uk_to_user = 100

        # === Now build your product dict (after fuzzy fixes)
        product = {
            "asin": asin,
            "title": title,
            "brand_estimated_origin": origin_country,
            "origin_city": origin_city,
            "distance_origin_to_uk": distance_origin_to_uk,
            "distance_uk_to_user": 100,
            "estimated_weight_kg": round(weight * 1.05, 2),
            "raw_product_weight_kg": weight,
            "dimensions_cm": dimensions,
            "material_type": material,
            "co2_emissions": None,
            "recyclability": recyclability,
            "transport_mode": transport_mode,
            "confidence": "High" if is_high_confidence({
                "material_type": material,
                "estimated_weight_kg": weight,
                "origin_city": origin_city
            }) else "Estimated"
        }
        
        # ✅ Now process + store it
        finalize_product_entry(product)
        return product


        # 🌍 Add missing distance fields
        origin_hub = origin_hubs.get(origin_country, origin_hubs["UK"])
        distance_origin_to_uk = round(haversine(origin_hub["lat"], origin_hub["lon"], uk_hub["lat"], uk_hub["lon"]), 1)
        distance_uk_to_user = 100  # static fallback — change if postcode logic is added

        product["distance_origin_to_uk"] = distance_origin_to_uk
        product["distance_uk_to_user"] = distance_uk_to_user
        print(f"🌍 Returning distances: {product.get('distance_origin_to_uk')} km from origin, {product.get('distance_uk_to_user')} km from UK hub")


        print("✅ Scraped product:", product["title"])
        print(f"🎯 Returning final origin: {origin_country} (source: {origin_source})")
        return product



    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass



# === SAVE TO FILE ===
def save_products_to_json(products, path="../ReactPopup/public/data.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    print(f"✅ Saved {len(products)} product(s) to {path}")

# === MAIN ===
if __name__ == "__main__":
    all_asins = set()
    all_products = []

    # Load priority DB
    priority_path = "priority_products.json"
    try:
        with open(priority_path, "r", encoding="utf-8") as f:
            priority_db = json.load(f)
            Log.success(f"🔐 Loaded {len(priority_db)} priority products.")
    except:
        priority_db = {}
        Log.warn("No existing priority_products.json, starting fresh.")

    # Define search terms
    search_terms = [
        "usb+c+charger", "eco+friendly+bottle", "coffee+mug", "mechanical+keyboard", 	
        "shampoo", "wireless+earbuds", "reusable+bag", "portable+fan", "toothbrush", 	
        "led+lamp", "bamboo cutlery", "compostable bag", "metal straw", "plastic container",
        "fabric tote", "glass bottle", "stainless steel mug", "wooden spoon",
        "eco friendly notebooks", "recycled stationery", "canvas shopping bag",
        "solar power bank", "eco friendly phone case" ,"stainless steel lunchbox",
        "reusable baking mat", "recycled paper towels", "compost bin kitchen", 
        "refillable deodorant", "eco friendly shampoo", "solid shampoo bar", "bamboo razor",
        "sustainable soap", "bamboo toothbrush", "reusable straws", "organic cotton bag"
    ]


    for term in search_terms:
        for page in range(1, 8):
            url = f"https://www.amazon.co.uk/s?k={term}&page={page}"
            Log.info(f"Scraping: {url}")
            products = scrape_amazon_titles(url, max_items=50)

            new_products = []
            for p in products:
                asin = p.get("asin")
                if asin and asin not in all_asins:
                    all_asins.add(asin)
                    new_products.append(p)

            if new_products:
                all_products.extend(new_products)
                Log.success(f"➕ {len(new_products)} new products")

            for p in new_products:
                asin = p.get("asin")
                maybe_add_to_priority(p, priority_db)
                Log.success(f"⭐ Added high-confidence product: {asin}")

            # Save priority products
        with open(priority_path, "w", encoding="utf-8") as f:
            json.dump(priority_db, f, indent=2)
            Log.success(f"✅ Saved {len(priority_db)} total trusted products.")

        with open("scraped_products_tmp.json", "w", encoding="utf-8") as f:
            json.dump(all_products, f, indent=2)
            Log.info(f"📥 Saved checkpoint: {len(all_products)} total")

        time.sleep(random.uniform(2.5, 4.5))  # anti-bot pause

    # ✅ ✅ NOW PROCESS THE PRODUCTS
    unique_products = {p["asin"]: p for p in all_products}.values()

    cleaned_products = []
    for product in unique_products:
        if is_high_confidence(product):
            cleaned_products.append({
                "title": product.get("title"),
                "material": product.get("material_type", "Other"),
                "weight": product.get("estimated_weight_kg", 0.5),
                "transport": product.get("transport_mode", "Land"),
                "recyclability": product.get("recyclability", "Medium"),
                "true_eco_score": "C",  # placeholder
                "co2_emissions": "",
                "origin": product.get("brand_estimated_origin", "Other")
            })

    with open("cleaned_products.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_products, f, indent=2)
        print(f"✅ Saved {len(cleaned_products)} to cleaned_products.json")

    if cleaned_products:
        import csv
        csv_path = os.path.join("ml_model", "real_scraped_dataset.csv")
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cleaned_products[0].keys())
            writer.writeheader()
            writer.writerows(cleaned_products)
            print(f"📄 Saved structured training data to {csv_path}")

    save_products_to_json(list(unique_products), "bulk_scraped_products.json")
