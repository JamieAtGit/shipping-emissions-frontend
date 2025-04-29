from flask import Flask, request, jsonify, session
from flask_cors import CORS
import joblib
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from Extension.scrape_amazon_titles import (scrape_amazon_product_page,estimate_origin_country, resolve_brand_origin,save_brand_locations)

import csv
import re

# === Load Flask ===
app = Flask(__name__)
app.secret_key = "super-secret-key"
CORS(app)

# === Load Model and Encoders ===
model_dir = "ml_model"
encoders_dir = os.path.join(model_dir, "encoders")

model = joblib.load(os.path.join(model_dir, "eco_model.pkl"))
material_encoder = joblib.load(os.path.join(encoders_dir, "material_encoder.pkl"))
transport_encoder = joblib.load(os.path.join(encoders_dir, "transport_encoder.pkl"))
recycle_encoder = joblib.load(os.path.join(encoders_dir, "recycle_encoder.pkl"))
label_encoder = joblib.load(os.path.join(encoders_dir, "label_encoder.pkl"))
origin_encoder = joblib.load(os.path.join(encoders_dir, "origin_encoder.pkl"))

valid_scores = list(label_encoder.classes_)
print("✅ Loaded label classes:", valid_scores)

# === Load CO2 Map ===
def load_material_co2_data():
    try:
        df = pd.read_csv(os.path.join(model_dir, "defra_material_intensity.csv"))
        return dict(zip(df["material"], df["co2_per_kg"]))
    except Exception as e:
        print(f"⚠️ Could not load DEFRA data: {e}")
        return {}

material_co2_map = load_material_co2_data()

# === Helpers ===
def normalize_feature(value, default):
    clean = str(value or default).strip().title()
    return default if clean.lower() == "unknown" else clean

def safe_encode(value, encoder, default):
    value = normalize_feature(value, default)
    if value not in encoder.classes_:
        print(f"⚠️ '{value}' not in encoder classes. Defaulting to '{default}'.")
        value = default
    return encoder.transform([value])[0]

@app.route("/api/feature-importance")
def get_feature_importance():
    try:
        importances = model.feature_importances_
        features = ["material", "weight", "transport", "recyclability", "origin"]
        data = [{"feature": f, "importance": round(i * 100, 2)} for f, i in zip(features, importances)]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




def to_python_type(obj):
    import numpy as np
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    return obj

@app.route("/predict", methods=["POST"])
def predict_eco_score():
    try:
        data = request.get_json()
        material = normalize_feature(data.get("material"), "Other")
        weight = float(data.get("weight") or 0.0)
        transport = normalize_feature(data.get("transport"), "Land")
        recyclability = normalize_feature(data.get("recyclability"), "Medium")
        origin = normalize_feature(data.get("origin"), "Other")

        # === Encode features
        material_encoded = safe_encode(material, material_encoder, "Other")
        transport_encoded = safe_encode(transport, transport_encoder, "Land")
        recycle_encoded = safe_encode(recyclability, recycle_encoder, "Medium")
        origin_encoded = safe_encode(origin, origin_encoder, "Other")

        X = [[material_encoded, weight, transport_encoded, recycle_encoded, origin_encoded]]
        prediction = model.predict(X)
        decoded_score = label_encoder.inverse_transform([prediction[0]])[0]

        confidence = 0.0
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)
            confidence = round(max(proba[0]) * 100, 1)

        # === Feature Importance *for this sample*
        global_importance = model.feature_importances_
        local_impact = {
            "material": to_python_type(material_encoded * global_importance[0]),
            "weight": to_python_type(weight * global_importance[1]),
            "transport": to_python_type(transport_encoded * global_importance[2]),
            "recyclability": to_python_type(recycle_encoded * global_importance[3]),
            "origin": to_python_type(origin_encoded * global_importance[4])
        }

        return jsonify({
            "predicted_label": decoded_score,
            "confidence": f"{confidence}%",
            "raw_input": {
                "material": material,
                "weight": weight,
                "transport": transport,
                "recyclability": recyclability,
                "origin": origin
            },
            "encoded_input": {
                "material": to_python_type(material_encoded),
                "weight": to_python_type(weight),
                "transport": to_python_type(transport_encoded),
                "recyclability": to_python_type(recycle_encoded),
                "origin": to_python_type(origin_encoded)
            },
            "feature_impact": local_impact
        })

    except Exception as e:
        print(f"❌ Error in /predict: {e}")
        return jsonify({"error": str(e)}), 500

# === Fuzzy Matching Helpers ===
def fuzzy_match_material(material):
    material_keywords = {
        "Plastic": ["plastic", "plastics"],
        "Glass": ["glass"],
        "Aluminium": ["aluminium", "aluminum"],
        "Steel": ["steel"],
        "Paper": ["paper", "papers"],
        "Cardboard": ["cardboard", "corrugated"],
    }

    material_lower = material.lower()
    for clean, keywords in material_keywords.items():
        if any(keyword in material_lower for keyword in keywords):
            return clean
    return material

def fuzzy_match_origin(origin):
    origin_keywords = {
        "China": ["china"],
        "UK": ["uk", "united kingdom"],
        "USA": ["usa", "united states", "america"],
        "Germany": ["germany"],
        "France": ["france"],
        "Italy": ["italy"],
    }

    origin_lower = origin.lower()
    for clean, keywords in origin_keywords.items():
        if any(keyword in origin_lower for keyword in keywords):
            return clean
    return origin

@app.route("/api/eco-data", methods=["GET"])
def fetch_eco_dataset():
    try:
        df = pd.read_csv("eco_dataset.csv")
        df = df.dropna(subset=["material", "true_eco_score", "co2_emissions"])
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        print(f"❌ Failed to return eco dataset: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/insights", methods=["GET"])
def insights_dashboard():
    try:
        # Load the logged data
        df = pd.read_csv("eco_dataset.csv")
        df = df.dropna(subset=["material", "true_eco_score", "co2_emissions"])  # Clean

        # Keep only the needed fields
        insights = df[["material", "true_eco_score", "co2_emissions"]]
        insights = insights.head(1000)  # Limit for frontend performance

        return jsonify(insights.to_dict(orient="records"))
    except Exception as e:
        print(f"❌ Failed to serve insights: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    try:
        data = request.get_json()
        feedback_dir = os.path.join("ml_model", "user_feedback.json")
        print("Received feedback:", data)
        # Append to file
        import json
        existing = []
        if os.path.exists(feedback_dir):
            with open(feedback_dir, "r") as f:
                existing = json.load(f)

        existing.append(data)

        with open(feedback_dir, "w") as f:
            json.dump(existing, f, indent=2)

        return jsonify({"message": "✅ Feedback saved!"}), 200

    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/estimate_emissions", methods=["POST"])
def estimate_emissions():
    try:
        data = request.get_json()
        url = data.get("amazon_url")
        include_packaging = data.get("include_packaging", True)

        if url:
            product = scrape_amazon_product_page(url)
            title = product.get("title", "Amazon Product")
            material = normalize_feature(product.get("material_type"), "Other")
            transport = normalize_feature(data.get("transport") or product.get("transport_mode"), "Land")
            recyclability = normalize_feature(product.get("recyclability"), "Medium")

            origin = normalize_feature(
                product.get("brand_estimated_origin") or product.get("origin"), 
                "Other"
            )

            if origin in ["Unknown", "Other", None, ""] and title:
                guessed = estimate_origin_country(title)
                if guessed and guessed.lower() != "other":
                    print(f"🧠 Fallback origin estimate from title: {guessed}")
                    origin = guessed
                else:
                    print(f"🔒 Skipped fallback — origin already trusted: {origin}")


            dimensions = product.get("dimensions_cm")
            raw_weight = product.get("raw_product_weight_kg")
            estimated_weight = product.get("estimated_weight_kg")

            try:
                weight = float(raw_weight or estimated_weight or 0.5)
            except:
                weight = 0.5

            if include_packaging:
                weight *= 1.05

            print(f"✅ Final product weight used: {weight} kg")


            raw_weight = product.get("raw_product_weight_kg")
            estimated_weight = product.get("estimated_weight_kg")
            weight = float(raw_weight or estimated_weight or 0.5)
            if include_packaging:
                weight *= 1.05

            try:
                weight = float(raw_weight or estimated_weight or 0.5)
            except:
                weight = 0.5

            if include_packaging:
                weight *= 1.05

            print(f"✅ Final product weight used: {weight} kg")

        else:
            title = data.get("title", "Manual Product")
            material = normalize_feature(data.get("material"), "Other")
            transport = normalize_feature(data.get("transport"), "Land")
            recyclability = normalize_feature(data.get("recyclability"), "Medium")
            origin = normalize_feature(data.get("origin"), "Other")
            dimensions = None

            try:
                weight = float(data.get("weight") or 0.5)
            except:
                weight = 0.5

            if include_packaging:
                weight *= 1.05

            print(f"✅ Final manual product weight used: {weight} kg")


        # Fuzzy material and origin mappings
        material = fuzzy_match_material(material)
        origin = fuzzy_match_origin(origin)

        # Calculate carbon
        carbon_kg = round(weight * material_co2_map.get(material, 2.0), 2)

        # ML prediction
        X = pd.DataFrame([[ 
            safe_encode(material, material_encoder, "Other"),
            weight,
            safe_encode(transport, transport_encoder, "Land"),
            safe_encode(recyclability, recycle_encoder, "Medium"),
            safe_encode(origin, origin_encoder, "Other")
        ]], columns=["material_encoded", "weight", "transport_encoded", "recycle_encoded", "origin_encoded"])

        decoded_score = "C"
        confidence = 0.0
        try:
            prediction = model.predict(X)[0]
            decoded_score = label_encoder.inverse_transform([prediction])[0]
            if decoded_score not in valid_scores:
                decoded_score = "C"
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X)
                confidence = round(max(proba[0]) * 100, 1)
            
        except Exception as e:
            print(f"⚠️ Prediction failed: {e}")

        # Logging
        try:
            log_path = os.path.join(model_dir, "eco_dataset.csv")
            with open(log_path, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerow([title, material, f"{weight:.2f}", transport, recyclability, decoded_score, carbon_kg, origin])
        except Exception as log_error:
            print(f"⚠️ Logging skipped: {log_error}")
            
            # 🔒 Log only real, valid scraped entries to a separate dataset for training
        try:
            if url:  # confirms this was a scraped product
                valid_materials = list(material_encoder.classes_)
                valid_transports = list(transport_encoder.classes_)
                valid_recyclability = list(recycle_encoder.classes_)
                valid_origins = list(origin_encoder.classes_)

                if (
                    decoded_score in valid_scores and
                    material in valid_materials and
                    transport in valid_transports and
                    recyclability in valid_recyclability and
                    origin in valid_origins
                ):
                    clean_log_path = os.path.join(model_dir, "real_scraped_dataset.csv")
                    with open(clean_log_path, "a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                        writer.writerow([title, material, f"{weight:.2f}", transport, recyclability, decoded_score, carbon_kg, origin])
                    print("✅ Logged to real_scraped_dataset.csv")
                else:
                    print("⚠️ Skipped real_scraped_dataset.csv log: one or more values are invalid.")
        except Exception as clean_log_error:
            print(f"⚠️ Logging to real_scraped_dataset.csv failed: {clean_log_error}")


        # Emojis
        emoji_map = {
            "A+": "🌍", "A": "🌿", "B": "🍃",
            "C": "🌱", "D": "⚠️", "E": "❌", "F": "💀"
        }
        print(f"🎯 Returning final origin: {origin}")

        import pprint
        pprint.pprint({
            "distance_from_origin_km": product.get("distance_origin_to_uk"),
            "distance_from_uk_hub_km": product.get("distance_uk_to_user")
        })


        return jsonify({
            "data": {
                "attributes": {
                    "eco_score_ml": f"{decoded_score} {emoji_map.get(decoded_score, '')} ({confidence}%)",
                    "eco_score_confidence": f"{confidence}%",
                    "ml_carbon_kg": round(weight * 1.2, 2),  # or whatever variable you're using
                    "trees_to_offset": max(1, round(carbon_kg / 15)),  # assumes 1 tree offsets ~15 kg CO₂/year
                    "material_type": material,
                    "weight_kg": round(weight, 2),  # weight incl packaging
                    "raw_product_weight_kg": round(raw_weight or estimated_weight or 0.5, 2),
                    "transport_mode": transport,
                    "recyclability": recyclability,
                    "origin": origin,
                    "dimensions_cm": dimensions,
                    "carbon_kg": round(carbon_kg, 2),
                    "distance_from_origin_km": float(product.get("distance_origin_to_uk", 0) or 0),
                    "distance_from_uk_hub_km": float(product.get("distance_uk_to_user", 0) or 0),
                
                },
                "title": title
            }
        })


    except Exception as e:
        print(f"❌ Uncaught error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/test_post", methods=["POST"])
def test_post():
    try:
        data = request.get_json()
        print("✅ Received test POST:", data)
        return jsonify({"message": "Success", "you_sent": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test')
def test():
    return "✅ Server is working!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)


@app.route("/health")
def health():
    return jsonify({"status": "✅ Server is up"}), 200

@app.route("/")
def home():
    return "<h2>🌍 EcoImpact API is Live</h2>"



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
