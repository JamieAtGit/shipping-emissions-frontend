from flask import Flask, request, jsonify
from flask_cors import CORS
from scrape_amazon_titles import scrape_amazon_product_page, haversine, origin_hubs, uk_hub
import pgeocode

app = Flask(__name__)
CORS(app)

# ✅ Add this helper function near the top
def determine_transport_mode(distance_km):
    if distance_km < 1500:
        return "Truck", 0.12  # 120g per tonne-km
    elif distance_km < 6000:
        return "Ship", 0.02   # 20g per tonne-km
    else:
        return "Air", 0.5     # 500g per tonne-km
    
def calculate_eco_score(carbon_kg, recyclability, distance_km, weight_kg):
    carbon_score = max(0, 10 - carbon_kg * 5)
    weight_score = max(0, 10 - weight_kg * 2)
    distance_score = max(0, 10 - distance_km / 1000)
    recycle_score = {
        "Low": 2,
        "Medium": 6,
        "High": 10
    }.get(recyclability or "Medium", 5)

    total_score = (carbon_score + weight_score + distance_score + recycle_score) / 4

    if total_score >= 9:
        return "A+"
    elif total_score >= 8:
        return "A"
    elif total_score >= 6.5:
        return "B"
    elif total_score >= 5:
        return "C"
    elif total_score >= 3.5:
        return "D"
    else:
        return "F"

@app.route("/estimate_emissions", methods=["POST"])
def estimate():
    data = request.get_json()
    url = data.get("amazon_url")
    postcode = data.get("postcode")
    include_packaging = data.get("include_packaging", True)
    override_mode = data.get("override_transport_mode")

    print(f"🌍 Request received: {url}")
    print(f"📍 Postcode: {postcode} | Packaging included? {include_packaging} | Override mode: {override_mode}")

    if not url or not postcode:
        return jsonify({'error': 'Missing URL or postcode'}), 400

    # Get lat/lon from postcode
    geo = pgeocode.Nominatim('gb')
    location = geo.query_postal_code(postcode)
    if location.empty or location.latitude is None:
        return jsonify({'error': 'Invalid postcode'}), 400

    user_lat, user_lon = location.latitude, location.longitude

    # Scrape product
    product = scrape_amazon_product_page(url)
    if not product:
        return jsonify({'error': 'Could not fetch product'}), 500

    print(f"🔍 Scraped product: {product.get('title', 'N/A')}")

    origin = origin_hubs.get(product['brand_estimated_origin'], uk_hub)

    # Distance from origin to user
    distance = haversine(origin['lat'], origin['lon'], user_lat, user_lon)
    product['distance_origin_to_user'] = round(distance, 1)

    # Distance from UK hub to user
    product['distance_uk_to_user'] = round(haversine(uk_hub['lat'], uk_hub['lon'], user_lat, user_lon), 1)

    # Raw + final weight
    raw_weight = product['estimated_weight_kg']
    final_weight = raw_weight * 1.2 if include_packaging else raw_weight

    # Transport mode decision
    transport_mode, emission_factor = determine_transport_mode(distance)
    modes = {
        "Air": 0.5,
        "Ship": 0.03,
        "Truck": 0.15
    }

    if override_mode in modes:
        transport_mode = override_mode
        emission_factor = modes[override_mode]

    carbon_kg = round(final_weight * emission_factor * (distance / 1000), 2)

    # Eco Score
    eco_score = calculate_eco_score(
        carbon_kg,
        product.get("recyclability"),
        product["distance_origin_to_user"],
        final_weight
    )

    # === 👇 Enhancement: fallback source flag + confidence
    origin_source = product.get("origin_source", "brand_db")
    confidence = product.get("confidence", "Estimated")

    # === ✅ Build response
    response = {
        "title": product.get("title"),
        "data": {
            "attributes": {
                "carbon_kg": carbon_kg,
                "weight_kg": round(final_weight, 2),
                "raw_product_weight_kg": round(raw_weight, 2),
                "origin": product['brand_estimated_origin'],
                "intl_distance_km": product['distance_origin_to_user'],
                "uk_distance_km": product['distance_uk_to_user'],
                "dimensions_cm": product.get("dimensions_cm"),
                "material_type": product.get("material_type"),
                "transport_mode": transport_mode,
                "emission_factors": modes,
                "eco_score": eco_score,
                "recyclability": product.get("recyclability"),
                "confidence": confidence,
                "origin_source": origin_source,
            }
        }
    }

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
