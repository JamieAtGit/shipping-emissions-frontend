from bs4 import BeautifulSoup
import requests

# Function to scrape CO2 emissions from a product page
def scrape_co2_emissions(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')

        # Example: Extract CO2 emissions based on a specific class
        co2_element = soup.find("span", {"class": "co2-emissions"})
        if co2_element:
            return co2_element.text.strip()
        else:
            print(f"CO2 emissions not found on {url}.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

# Function to fetch emissions data from Carbon Interface API
def get_emissions(weight, distance, api_key="28rYCUXK2Wdbv0EjvYaFg"):
    try:
        url = "https://www.carboninterface.com/api/v1/estimates"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "type": "shipment",
            "weight_value": weight,
            "weight_unit": "kg",
            "distance_value": distance,
            "distance_unit": "km"
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error with API request: {e}")
        return None
    
    
def detect_origin_from_text(text):
    text = text.lower()
    if "made in china" in text or "country of origin: china" in text:
        return "China"
    elif "made in germany" in text or "country of origin: germany" in text:
        return "Germany"
    elif "made in usa" in text or "country of origin: usa" in text:
        return "USA"
    elif "made in japan" in text:
        return "Japan"
    # Add more if needed
    return None


# Main logic
if __name__ == "__main__":
    # Example 1: Scrape CO2 emissions from a product page
    product_url = "https://example.com/product-page"  # Replace with the actual URL
    co2_emissions = scrape_co2_emissions(product_url)
    if co2_emissions:
        print(f"Scraped CO2 emissions: {co2_emissions}")

    # Example 2: Fetch emissions data from API
    weight = 5  # Weight in kg
    distance = 1000  # Distance in km
    api_response = get_emissions(weight, distance)
    if api_response:
        print("API Response:", api_response)
