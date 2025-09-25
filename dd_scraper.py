#!/usr/bin/env python3
"""
DamaDam Profile Scraper – Fixed version with:
- open_by_key Google Sheet method
- Robust login button fallback
- Extra waits for headless mode
"""

import os
import sys
import time
import csv
import json
import random
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = WHITE = CYAN = MAGENTA = ""
    class Style:
        RESET_ALL = ""

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

# === CONFIGURATION ===
LOGIN_URL = "https://damadam.pk/login/"
ONLINE_USERS_URL = "https://damadam.pk/online_kon/"
USERNAME = os.getenv("DD_USERNAME") or "0utLawZ"
PASSWORD = os.getenv("DD_PASSWORD") or "@Brandex1999"

COOKIES_FILE = "DD-cookiess.json"
CSV_OUTPUT = "DD-profiless.csv"
SERVICE_JSON = "online.json"
# Use your sheet ID from URL:
SPREADSHEET_ID = "1XQxDCZYy47oqA5-4PdZ1X_WO4Jhy1BIWWNmXBqJX-FE"

# Google Sheet export config
EXPORT_TO_GOOGLE_SHEETS = True
LOOP_WAIT_MINUTES = 15

# Delays
MIN_DELAY = 0.5
MAX_DELAY = 1.5
LOGIN_DELAY = 5
PAGE_LOAD_TIMEOUT = 10

FIELDNAMES = [
    "DATE", "TIME", "NICKNAME", "TAGS", "CITY",
    "GENDER", "MARRIED", "AGE", "JOINED", "FOLLOWERS",
    "POSTS", "PLINK", "PIMAGE", "INTRO"
]

global_driver = None

def log_msg(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": Fore.WHITE, "SUCCESS": Fore.GREEN, "WARNING": Fore.YELLOW, "ERROR": Fore.RED}
    color = colors.get(level, Fore.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")

# === Browser setup ===
def setup_fast_browser():
    try:
        log_msg("🚀 Setting up browser...", "INFO")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # optional performance flags
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        # Anti-detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        log_msg(f"❌ Browser setup error: {e}", "ERROR")
        return None

# === Cookie loading ===
def smart_load_cookies(driver):
    try:
        if not os.path.exists(COOKIES_FILE):
            return False
        driver.get("https://damadam.pk")
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.get(ONLINE_USERS_URL)
        time.sleep(1)
        if "online_kon" in driver.current_url:
            log_msg("✅ Cookies loaded", "SUCCESS")
            return True
        return False
    except Exception as e:
        log_msg(f"Cookie load failed: {e}", "WARNING")
        return False

def save_cookies(driver):
    try:
        with open(COOKIES_FILE, "w") as f:
            json.dump(driver.get_cookies(), f)
        return True
    except Exception as e:
        return False

# === Login with fallback ===
def fast_login(driver):
    try:
        log_msg("🔐 Logging in...", "INFO")
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, LOGIN_DELAY)
        # Wait until page body is loaded
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Try primary click
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()
        except TimeoutException:
            # Fallback: maybe text is "Log In" or "Sign in"
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Log In") or contains(text(),"Sign in")]'))).click()
        # Now username / password fields
        wait.until(EC.presence_of_element_located((By.NAME, "nick"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "pass").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "form button").click()
        # Wait for redirect
        t0 = time.time()
        while time.time() - t0 < LOGIN_DELAY:
            if "login" not in driver.current_url.lower():
                save_cookies(driver)
                log_msg("✅ Login successful", "SUCCESS")
                return True
            time.sleep(0.2)
        return False
    except Exception as e:
        log_msg(f"❌ Login error: {e}", "ERROR")
        return False

# === Get online users ===
def get_online_users_fast(driver):
    try:
        driver.get(ONLINE_USERS_URL)
        wait = WebDriverWait(driver, PAGE_LOAD_TIMEOUT)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li bdi")))
        elems = driver.find_elements(By.CSS_SELECTOR, "li bdi")
        users = list({el.text.strip() for el in elems if el.text.strip()})
        log_msg(f"✅ Found {len(users)} online users", "SUCCESS")
        return users
    except Exception as e:
        log_msg(f"Error getting users: {e}", "ERROR")
        return []

# === Scrape profile ===
def scrape_profile_fast(driver, nickname):
    url = f"https://damadam.pk/users/{nickname}/"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.cxl.clb.lsp")))
        now = datetime.now()
        data = {
            'DATE': now.strftime("%d-%b-%Y"),
            'TIME': now.strftime("%I:%M %p"),
            'NICKNAME': nickname,
            'TAGS': '', 'CITY': '', 'GENDER': '',
            'MARRIED': '', 'AGE': '', 'JOINED': '',
            'FOLLOWERS': '', 'POSTS': '',
            'PLINK': url,
            'PIMAGE': '', 'INTRO': ''
        }
        try:
            data['INTRO'] = clean_text(driver.find_element(By.CSS_SELECTOR, ".ow span.nos").text)
        except:
            pass
        fields = {'City:': 'CITY', 'Gender:': 'GENDER', 'Married:': 'MARRIED', 'Age:': 'AGE', 'Joined:': 'JOINED'}
        for f, key in fields.items():
            try:
                val = driver.find_element(By.XPATH, f"//b[contains(text(), '{f}')]/following-sibling::span[1]").text
                data[key] = extract_numbers(val) if key == "JOINED" else clean_text(val)
            except:
                pass
        try:
            data['FOLLOWERS'] = re.search(r'(\d+)', driver.find_element(By.CSS_SELECTOR, "span.cl.sp.clb").text).group(1)
        except:
            pass
        try:
            data['POSTS'] = clean_text(driver.find_element(By.CSS_SELECTOR, "a[href*='/profile/public/'] button div:first-child").text)
        except:
            pass
        try:
            data['PIMAGE'] = driver.find_element(By.CSS_SELECTOR, "img[src*='avatar-imgs']").get_attribute('src')
        except:
            pass
        return data
    except Exception as e:
        log_msg(f"Error scraping {nickname}: {e}", "ERROR")
        return None

def clean_text(text):
    if not text:
        return ""
    t = str(text).strip().replace('\xa0', ' ').replace('+', '')
    if t.lower() in ['not set', 'no set', 'no city']:
        return ""
    return re.sub(r'\s+', ' ', t).strip()

def extract_numbers(text):
    if not text:
        return ""
    nums = re.findall(r'\d+', str(text))
    return ', '.join(nums) if nums else clean_text(text)

# === Google Sheets export ===
def export_to_google_sheets(profiles_batch):
    if not GOOGLE_SHEETS_AVAILABLE or not EXPORT_TO_GOOGLE_SHEETS or not profiles_batch:
        return False
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        # Prepare rows: convert dict to list in same order as FIELDNAMES plus an SCOUNT
        rows = []
        for prof in profiles_batch:
            row = [prof.get(fn, "") for fn in FIELDNAMES]
            row.append("1")  # initial seen count
            rows.append(row)
        sheet.append_rows(rows)
        log_msg(f"📤 Exported {len(rows)} to Google Sheets", "SUCCESS")
        return True
    except Exception as e:
        log_msg(f"Google Sheets export error: {e}", "ERROR")
        return False

# === Main scraping logic ===
def main_optimized(reuse_browser=False):
    global global_driver
    if reuse_browser and global_driver:
        driver = global_driver
    else:
        driver = setup_fast_browser()
        if not driver:
            return []
        if not smart_load_cookies(driver):
            if not fast_login(driver):
                log_msg("Authentication failed", "ERROR")
                driver.quit()
                return []
        if reuse_browser:
            global_driver = driver

    users = get_online_users_fast(driver)
    if not users:
        if not reuse_browser:
            driver.quit()
        return []

    stats = {"total": len(users), "current": 0, "success": 0, "errors": 0}
    scraped = []

    with open(CSV_OUTPUT, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if f.tell() == 0:
            writer.writeheader()

        for i, nick in enumerate(users, start=1):
            stats["current"] = i
            prof = scrape_profile_fast(driver, nick)
            if prof:
                writer.writerow(prof)
                scraped.append(prof)
                stats["success"] += 1
                # Batch export every 10
                if len(scraped) % 10 == 0:
                    export_to_google_sheets(scraped[-10:])
            else:
                stats["errors"] += 1
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        # Export remaining
        rem = len(scraped) % 10
        if rem > 0:
            export_to_google_sheets(scraped[-rem:])

    if not reuse_browser:
        driver.quit()

    return scraped

def run_continuous_optimized():
    global global_driver
    loop = 0
    try:
        while True:
            loop += 1
            log_msg(f"🔄 Run #{loop}", "INFO")
            main_optimized(reuse_browser=True)
            log_msg("Sleeping next run...", "INFO")
            for s in range(LOOP_WAIT_MINUTES * 60, 0, -1):
                mins, secs = divmod(s, 60)
                print(f"\r⏱ Next in {mins:02d}:{secs:02d}", end="", flush=True)
                time.sleep(1)
            print()
    except KeyboardInterrupt:
        log_msg("Stopped by user", "WARNING")
    finally:
        if global_driver:
            global_driver.quit()
            global_driver = None

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}🚀 DamaDam Scraper (Fixed){Style.RESET_ALL}")
    print("1. Run once (optimized)")
    print("2. Continuous loop")
    print("3. Exit")
    choice = input("Choose (1-3): ")
    if choice == "1":
        main_optimized(reuse_browser=False)
    elif choice == "2":
        run_continuous_optimized()
    else:
        log_msg("Exiting", "INFO")
