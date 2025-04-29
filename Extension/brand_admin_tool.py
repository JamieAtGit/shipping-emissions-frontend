import csv
import os

UNRECOGNIZED_FILE = "unrecognized_brands.txt"
BRAND_CSV = "brand_origins.csv"

def load_unrecognized_brands():
    if not os.path.exists(UNRECOGNIZED_FILE):
        print("✅ No unrecognized brands to process.")
        return []
    with open(UNRECOGNIZED_FILE, "r", encoding="utf-8") as f:
        return sorted(set([line.strip().lower() for line in f if line.strip()]))

def append_to_csv(brand, country, city):
    with open(BRAND_CSV, "a", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["brand", "hq_country", "hq_city"])
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow({"brand": brand, "hq_country": country, "hq_city": city})

def admin_loop():
    brands = load_unrecognized_brands()
    if not brands:
        return

    remaining = []

    print(f"\n🎯 Reviewing {len(brands)} unrecognized brands...\n")
    for brand in brands:
        print(f"🔍 Brand: {brand}")
        action = input("Add (a), Skip (s), Delete (d)? ").strip().lower()

        if action == "a":
            country = input("  🌍 Country: ").strip()
            city = input("  🏙️  City: ").strip()
            append_to_csv(brand, country, city)
            print(f"✅ Added '{brand}' to CSV.\n")

        elif action == "s":
            remaining.append(brand)
            print("⏭️ Skipped.\n")

        elif action == "d":
            print("❌ Deleted.\n")

        else:
            print("⚠️ Invalid input. Skipping.\n")
            remaining.append(brand)

    with open(UNRECOGNIZED_FILE, "w", encoding="utf-8") as f:
        for b in remaining:
            f.write(f"{b}\n")

    print("\n✅ Finished. Remaining unrecognized brands saved.")

if __name__ == "__main__":
    admin_loop()
