import requests
import json

API_KEY = "YOUR_API_KEY"  # Replace with your actual key

def fetch_emissions(weight, distance):
    url = "https://www.carboninterface.com/api/v1/estimates"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "type": "shipment",
        "weight_value": weight,
        "weight_unit": "kg",
        "distance_value": distance,
        "distance_unit": "km"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code}, {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def update_data(products):
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("data.json not found. Creating a new file...")
        data = {}

    for product in products:
        if product["name"] not in data:
            print(f"Fetching data for {product['name']}...")
            api_data = fetch_emissions(product["weight"], product["distance"])
            if api_data:
                co2_emissions = api_data["data"]["attributes"]["carbon_kg"]
                data[product["name"]] = {
                    "co2_emissions": co2_emissions,
                    "recyclability": "Unknown",
                    "waste": "Unknown",
                    "lifecycle_impact": {
                        "manufacturing": "N/A",
                        "shipping": co2_emissions,
                        "disposal": "N/A"
                    }
                }

    with open("data.json", "w") as file:
        json.dump(data, file, indent=2)
    print("Data.json updated successfully.")

if __name__ == "__main__":
    products_to_update = [
        {"name": "Protein Powder A", "weight": 5, "distance": 1000},
        {"name": "Protein Powder B", "weight": 4, "distance": 1200},
    ]
    update_data(products_to_update)
