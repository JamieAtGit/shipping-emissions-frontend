import time
import random
import json
import os
import csv
from datetime import datetime
from scrape_amazon_titles import scrape_amazon_titles, is_high_confidence, Log

# === CONFIG ===
priority_path = "priority_products.json"
bulk_path = "bulk_scraped_products.json"
log_path = "logs/scheduler_log.txt"
backup_dir = "backups"
search_terms_csv = "search_terms.csv"
failed_urls_path = "failed_urls.txt"
blocked_urls_path = "blocked_urls.txt"
retry_tracker_path = "blocked_urls_retry.txt"
pages_per_term = 2  # You can increase this later
sleep_between_jobs = (600, 1200)  # 10–20 mins
backup_every_n_loops = 5

# === LOAD SEARCH TERMS ===
def load_terms_from_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [row[0] for row in csv.reader(f) if row]

search_terms = load_terms_from_csv(search_terms_csv)
if not search_terms:
    search_terms = [
        "usb+c+charger", "eco+friendly+bottle", "coffee+mug",
        "mechanical+keyboard", "shampoo", "wireless+earbuds",
        "reusable+bag", "portable+fan", "toothbrush", "led+lamp",
        "recycled+notebook", "bamboo+cutlery", "solar+power+bank"
    ]

# === LOAD DBs ===
priority_db = {}
if os.path.exists(priority_path):
    with open(priority_path, "r", encoding="utf-8") as f:
        priority_db = json.load(f)

bulk_db = []
if os.path.exists(bulk_path):
    with open(bulk_path, "r", encoding="utf-8") as f:
        bulk_db = json.load(f)

existing_asins = {p["asin"] for p in bulk_db if p.get("asin")}
seen_urls = set()
loop_count = 0

# === LOGGING ===
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line.strip())
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
        

def maybe_add_to_priority(product, priority_db, priority_path):
    asin = product.get("asin")
    if not asin or asin in priority_db:
        return False

    if is_high_confidence(product):
        product["confidence"] = "High"
        priority_db[asin] = product
        with open(priority_path, "w", encoding="utf-8") as f:
            json.dump(priority_db, f, indent=2)
        Log.success(f"🔐 Added {asin} to priority_products.json")
        return True
    return False


failed_urls_path = "failed_urls.txt"

def save_failed_url(url):
    with open(failed_urls_path, "a", encoding="utf-8") as f:
        f.write(url + "\n")
        

def load_failed_urls():
    if not os.path.exists(failed_urls_path):
        return []
    with open(failed_urls_path, "r", encoding="utf-8") as f:
        return list(set(line.strip() for line in f if line.strip()))

def remove_url_from_failed(url):
    if not os.path.exists(failed_urls_path):
        return
    with open(failed_urls_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = [line for line in lines if line.strip() != url]
    with open(failed_urls_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
def load_blocked_urls():
    if not os.path.exists(blocked_urls_path):
        return []
    with open(blocked_urls_path, "r", encoding="utf-8") as f:
        return list(set(line.strip() for line in f if line.strip()))

def move_to_retry_tracker(url):
    with open(retry_tracker_path, "a", encoding="utf-8") as f:
        f.write(url + "\n")
    if os.path.exists(blocked_urls_path):
        with open(blocked_urls_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and line.strip() != url]
        with open(blocked_urls_path, "w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in lines)


retry_queue = load_failed_urls()

# === MAIN LOOP ===
while True:
    retry_mode = False
    blocked_urls = load_blocked_urls()
    if blocked_urls and random.random() < 0.5:  # try blocked URLs sometimes
        url = random.choice(blocked_urls)
        log(f"⚠️ Retrying previously blocked URL: {url}")
        retry_mode = True
    else:
        term = random.choice(search_terms)
        page = random.randint(1, pages_per_term)
        url = f"https://www.amazon.co.uk/s?k={term}&page={page}"
    
    # Retry logic
    if not retry_mode and retry_queue:
        url = retry_queue.pop()
        log(f"♻️ Retrying failed URL: {url}")


    if url in seen_urls:
        log("⚠️ Already tried this URL, skipping.")
        continue
    seen_urls.add(url)

    log(f"🌐 Scraping: {url}")
    try:
        scraped = scrape_amazon_titles(url, max_items=30)
    except Exception as e:
        log(f"❌ Error scraping {url}: {e}")
        if retry_mode:
            move_to_retry_tracker(url)
        else:
            save_failed_url(url)
        time.sleep(10)
        continue



    new_bulk = []
    new_priority = 0

    for product in scraped:
        asin = product.get("asin")
        if not asin or asin in existing_asins:
            continue

        existing_asins.add(asin)
        new_bulk.append(product)

        if maybe_add_to_priority(product, priority_db, priority_path):
            new_priority += 1

    if new_bulk:
        remove_url_from_failed(url)
        bulk_db.extend(new_bulk)
        log(f"➕ Added {len(new_bulk)} new products. {new_priority} high-confidence.")

        with open(bulk_path, "w", encoding="utf-8") as f:
            json.dump(bulk_db, f, indent=2)

        with open(priority_path, "w", encoding="utf-8") as f:
            json.dump(priority_db, f, indent=2)

    else:
        log("🤷 No new unique products found.")

    # 🔁 Periodic Backup
    loop_count += 1
    if loop_count % backup_every_n_loops == 0:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"{backup_dir}/bulk_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(bulk_db, f, indent=2)
        with open(f"{backup_dir}/priority_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(priority_db, f, indent=2)
        log("💾 Backup created.")

    # 💤 Sleep before next round
    delay = random.randint(*sleep_between_jobs)
    log(f"⏲️ Sleeping for {delay // 60} mins...")
    time.sleep(delay)
