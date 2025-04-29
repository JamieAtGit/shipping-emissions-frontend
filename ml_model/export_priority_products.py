import json
import csv

input_path = "priority_products.json"
output_path = "eco_dataset.csv"

# Load product data
with open(input_path, "r", encoding="utf-8") as f:
    products = json.load(f)

fields = ["material", "weight", "transport", "recyclability", "origin", "true_eco_score"]

with open(output_path, "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for asin, product in products.items():
        row = {
            "material": product.get("material_type", "Other"),
            "weight": product.get("estimated_weight_kg", 0.5),
            "transport": "Land",  # default assumption
            "recyclability": product.get("recyclability", "Unknown").title(),
            "origin": product.get("brand_estimated_origin", "Unknown"),
            "true_eco_score": ""  # <-- You will fill this manually (A+, A, B, ...)
        }
        writer.writerow(row)

print(f"✅ Exported {len(products)} rows to {output_path}")
