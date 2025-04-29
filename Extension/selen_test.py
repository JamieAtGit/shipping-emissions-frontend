from undetected_chromedriver import Chrome
import time

print("🚀 Launching Chrome...")
driver = Chrome(headless=False)
driver.get("https://www.amazon.co.uk/dp/B0BGJTK8Z6")
print("✅ Page loaded.")
time.sleep(10)
driver.quit()
