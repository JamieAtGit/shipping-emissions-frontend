# test_batch.py
import requests

products = [
    {
        "name": "Fritz Repeater",
        "url": "https://www.amazon.co.uk/dp/B0BSR4X8Q8",
        "postcode": "M13 9PL"
    },
    {
        "name": "Huel Powder",
        "url": "https://www.amazon.co.uk/dp/B0DCCYFL1S",
        "postcode": "M13 9PL"
    },
    {
        "name": "UK Map",
        "url": "https://www.amazon.co.uk/dp/B079T671F3",
        "postcode": "M13 9PL"
    }
]

for item in products:
    print(f"\n🔎 Testing: {item['name']}")
    res = requests.post("http://127.0.0.1:5000/estimate_emissions", json={
        "amazon_url": item["url"],
        "postcode": item["postcode"]
    })
    try:
        print("✅ Status:", res.status_code)
        print("📦 Response:", res.json())
    except Exception as e:
        print("❌ Failed to parse response:", e)
        print("Raw:", res.text)
