import json
import os

# Load brand_locations.json
brand_locations_path = "brand_locations.json"
if os.path.exists(brand_locations_path):
    with open(brand_locations_path, "r", encoding="utf-8") as f:
        brand_locations = json.load(f)
else:
    brand_locations = {}

# Load unrecognized_brands.txt
with open("unrecognized_brands.txt", "r", encoding="utf-8") as f:
    unreviewed_brands = sorted(set([line.strip() for line in f if line.strip()]))

updated = 0

for brand in unreviewed_brands[:]:
    if brand in brand_locations:
        print(f"✅ {brand} already exists. Skipping.")
        continue

    print(f"\n🔍 Reviewing brand: {brand}")
    country = input("🌍 Enter origin country (or leave blank to skip): ").strip()
    if not country:
        continue

    city = input("🏙️  Enter origin city (optional): ").strip() or "Unknown"

    brand_locations[brand] = {
        "origin": {
            "country": country,
            "city": city
        },
        "fulfillment": "UK"
    }
    updated += 1

    # Remove from the list once reviewed
    unreviewed_brands.remove(brand)

# Save updated brand_locations.json
with open(brand_locations_path, "w", encoding="utf-8") as f:
    json.dump(brand_locations, f, indent=2)
    print(f"\n✅ Updated brand_locations.json with {updated} new entries.")

# Overwrite unrecognized_brands.txt with remaining
with open("unrecognized_brands.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(unreviewed_brands))
    print(f"🧹 Cleaned up unrecognized_brands.txt (remaining: {len(unreviewed_brands)})")
