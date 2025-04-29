from undetected_chromedriver import Chrome

driver = Chrome(headless=False)  # ⬅️ This will open a visible browser window
driver.get("https://www.amazon.co.uk/dp/B0BGJTK8Z6")

input("🔍 Press Enter after checking if the page loads properly...")
driver.quit()
