# ml_model/generate_dataset.py

import csv
import sys
import os

# Ensure import from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ✅ Import the scraping function (make sure this is the one you're using)
from Extension.scrape_amazon_titles import scrape_amazon_product

# 🔗 Add Amazon product URLs here
amazon_urls = [
    "https://www.amazon.co.uk/dp/B09G9D8KRQ",
    "https://www.amazon.co.uk/dp/B07PGL2N7J",
    "https://www.amazon.co.uk/dp/B08N5WRWNW",
    "https://www.amazon.co.uk/dp/B07FZ8S74R",
    "https://www.amazon.co.uk/dp/B08Z7ZJFBG",
]

rows = []

for url in amazon_urls:
    try:
        product = scrape_amazon_product(url)

        if product is None:
            print(f"⚠️ Skipping empty result for {url}")
            continue

        material = product.get("material_type", "Unknown")
        weight = product.get("weight_kg", 0.5)
        transport = product.get("transport_mode", "Land")
        carbon = product.get("carbon_kg")

        if carbon is None:
            print(f"⚠️ Skipping product with missing carbon value from {url}")
            continue

        # 🌱 Define a pseudo "true" eco score based on carbon output
        if carbon < 0.4:
            score = "A+"
        elif carbon < 0.7:
            score = "A"
        elif carbon < 1.0:
            score = "B"
        elif carbon < 1.5:
            score = "C"
        elif carbon < 2.0:
            score = "D"
        else:
            score = "F"

        rows.append([material, weight, transport, score])
        print(f"✅ Scraped: {product.get('title')}")

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")

# 💾 Save to CSV
os.makedirs("ml_model", exist_ok=True)
with open("ml_model/eco_dataset.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["material", "weight", "transport", "true_eco_score"])
    writer.writerows(rows)

print(f"✅ Saved {len(rows)} products to eco_dataset.csv")
