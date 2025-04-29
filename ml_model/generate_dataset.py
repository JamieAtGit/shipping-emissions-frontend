import csv
import os
import time
import random
from random import choice, uniform

# --- Config ---
search_terms = [
    "reusable water bottle", "bamboo toothbrush", "led desk lamp", "mouse",
    "eco tote bag", "solar charger", "compost bin", "glass food container",
    "protein powder", "iphone", "electric guitar", "amplifier", "office chair",
    "notepad", "pencils", "snowboard", "aftershave", "canvas", "deodrant",
    "lighter", "laptop", "bicycle", "hammer", "chopping board", "hammock"
    "photo frame", "books", "plant pot", "piano", "clock", "portable charger",
    "cat food", "vinyl", "headphones", "marker", "moisturiser", "playstation",
    "beanie", "necklace", "extension cord", "nail clippers", "glow sticks", "fork"
]
max_products = 100
rows = []

origins = ["UK", "China", "Germany", "USA", "Italy", "France", "Singapore", "Brazil", "India", "Norway", "Russia", "Japan"]

# --- Eco scoring logic ---
def assign_recyclability(material):
    if material in ["Plastic"]:
        return "Low"
    elif material in ["Glass", "Aluminum", "Steel"]:
        return "High"
    elif material in ["Bamboo", "Cardboard", "Paper"]:
        return "Medium"
    else:
        return choice(["Low", "Medium", "High"])  # fallback randomness


def assign_score(material, weight, transport):
    if material == "Bamboo" and transport == "Ship" and weight < 0.5:
        return "A+"
    if transport == "Air":
        return "F"
    if weight > 1.2:
        return "D"
    if material == "Plastic" and transport == "Land":
        return "C"
    if material == "Glass" and transport == "Ship":
        return "B"
    if material == "Steel":
        return "C"
    return random.choice(["A", "B", "C", "D", "E", "F"])  # fallback randomness

def mock_product():
    material = choice(materials)
    transport = choice(["Land", "Air", "Ship"])
    weight = round(uniform(0.1, 2.0), 2)
    recyclability = assign_recyclability(material)
    origin = choice(origins).upper()   # randomly pick one

    base = {
        "Plastic": 1.2,
        "Bamboo": 0.6,
        "Glass": 1.5,
        "Steel": 1.8,
        "Cardboard": 0.7,
        "Aluminum": 1.6,
        "Paper": 0.5
    }.get(material, 1.0)  # 👈 fallback for 'Other' or unexpected material
    print("🔬 Material chosen:", material)


    transport_factor = {
        "Land": 1.0,
        "Air": 2.5,
        "Ship": 0.8
    }[transport]

    recycle_factor = {
    "Low": 1.0,
    "Medium": 0.9,
    "High": 0.7
    }.get(recyclability, 1.0)  # 👈 Default to 1.0 if 'Unknown'


    carbon = round(weight * base * transport_factor * recycle_factor, 2)

    return {
        "material": material,
        "weight": weight,
        "transport": transport,
        "recyclability": recyclability,
        "co2_emissions": carbon,
        "origin": origin  # 👈 NEW
    }


# --- Generate data ---
materials = ["Plastic", "Bamboo", "Other", "Glass", "Steel", "Cardboard", "Aluminum", "Paper",]

for term in search_terms:
    print(f"\n🔎 Searching: {term}")
    for _ in range(max_products):
        product = mock_product()
        eco_score = assign_score(product["material"], product["weight"], product["transport"])

        rows.append([
            term,  # ➜ this is the new "title" field
            product["material"],
            product["weight"],
            product["transport"],
            product["recyclability"],
            eco_score,
            product["co2_emissions"],
            product["origin"]
        ])

        
        print(f"✅ Mock Eco Product ➜ {eco_score}")
        time.sleep(random.uniform(0.1, 0.2))  # faster runs

# --- Save to CSV ---
base_dir = os.path.dirname(__file__)
save_path = os.path.join(base_dir, "eco_dataset.csv")

print(f"\n🧮 Total rows generated: {len(rows)}")
print(f"📄 Saving to: {os.path.abspath(save_path)}")
print("🔍 Example row with title:", rows[0])

with open(save_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title","material", "weight", "transport", "recyclability", "true_eco_score", "co2_emissions", "origin"])
    writer.writerows(rows)

print(f"\n✅ Saved {len(rows)} smart mock products to {save_path}")
