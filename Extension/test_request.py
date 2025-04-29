import requests

url = "http://127.0.0.1:5000/estimate_emissions"
payload = {
    "amazon_url": "https://www.amazon.co.uk/Kinetica-Protein-Powder-Servings-2-27kg/dp/B08FMNYJYT/ref=sr_1_1_sspa?dib=eyJ2IjoiMSJ9.6VcV697VL7aNqxQQyhXamq39oZMvGP1JL0vMwxvyV_diaNMXICVrJm3Hg8yowjuVE9QEWHzmgIpo8HANsEPPUkypo7blOtQMc1QWjOMYxf1l2GVxOXl6eZSAK8G3jyng312A0PgjfyPio_2GEJhv9VeuIWkrxGyt6PU8ZPtduuIhaDIqihzszF4-MSq9eEc0sQKBGr-aTyEBGEGm7sH8sWeT5yHju9jxIWlUQ7P255v718CfKGWV_Cu-JOHInMhvz8Alu1R9yLxIk_-jXQ1ZT5Q57O42Q_WTziIK3tgZm0Q.dO54z7edkA_DxuBZi6rEcqOmbO238p4LfKT7Esmzai0&dib_tag=se&keywords=protein%2Bpowder&qid=1744570685&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1",  # Use a real product link
    "postcode": "SW1A 1AA",
    "include_packaging": True
}

try:
    print(f"📡 Sending POST to: {url}")
    response = requests.post(url, json=payload, timeout=120)
    print("📥 Got response:")
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(f"❌ Request failed: {e}")
