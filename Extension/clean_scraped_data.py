import json
import csv
import argparse
from collections import defaultdict

# === CONFIG ===
INPUT_JSON = "bulk_scraped_products.json"
OUTPUT_JSON = "cleaned_products.json"
OUTPUT_CSV = "cleaned_products.csv"

def load_products(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return []

def deduplicate(products):
    deduped = {}
    for p in products:
        asin = p.get("asin")
        if asin and asin not in deduped:
            deduped[asin] = p
    return list(deduped.values())

def filter_by_confidence(products, level="All"):
    if level == "All":
        return products
    return [p for p in products if p.get("confidence", "").lower() == level.lower()]

def export_json(products, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    print(f"✅ Exported JSON: {path} ({len(products)} products)")

def export_csv(products, path):
    if not products:
        print("⚠️ No products to export.")
        return

    keys = [
        "asin", "title", "estimated_weight_kg", "dimensions_cm", "material_type",
        "brand_estimated_origin", "origin_city", "confidence", "recyclability"
    ]

    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for p in products:
            writer.writerow({k: p.get(k, "") for k in keys})

    print(f"📄 CSV exported: {path}")

def main(confidence_filter, csv_export, top_n=None):
    raw = load_products(INPUT_JSON)
    print(f"📥 Loaded: {len(raw)} products")

    deduped = deduplicate(raw)
    print(f"🧼 Deduplicated: {len(deduped)} unique ASINs")

    filtered = filter_by_confidence(deduped, confidence_filter)
    print(f"🔍 Filtered: {len(filtered)} products with confidence='{confidence_filter}'")

    if top_n:
        filtered = filtered[:top_n]
        print(f"🔢 Top N limited to: {top_n} entries")

    export_json(filtered, OUTPUT_JSON)

    if csv_export:
        export_csv(filtered, OUTPUT_CSV)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🧼 Clean and export Amazon product data.")
    parser.add_argument("--confidence", choices=["All", "High", "Estimated"], default="All", help="Confidence level to filter by")
    parser.add_argument("--csv", action="store_true", help="Export to CSV")
    parser.add_argument("--top", type=int, help="Only include top N results")

    args = parser.parse_args()
    main(confidence_filter=args.confidence, csv_export=args.csv, top_n=args.top)
