#!/usr/bin/env python3
"""
DamaDam Profile Scraper - GITHUB ACTIONS VERSION
Optimized for cloud execution with Google Sheets integration
"""

import os
import sys
import time
import json
import random
import re
from datetime import datetime

print("🚀 Starting DamaDam Scraper (GitHub Actions Version)...")

# Check required packages
missing_packages = []

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    print("✅ Selenium ready")
except ImportError:
    missing_packages.append("selenium webdriver-manager")

try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    print("✅ Colors ready")
except ImportError:
    missing_packages.append("colorama")
    class Fore:
        CYAN = GREEN = YELLOW = RED = WHITE = MAGENTA = BLUE = ""
    class Style:
        RESET_ALL = ""

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    print("✅ Google Sheets ready")
except ImportError:
    missing_packages.append("gspread oauth2client")

if missing_packages:
    print(f"❌ Missing packages: {missing_packages}")
    sys.exit(1)

# === CONFIGURATION FROM ENVIRONMENT VARIABLES ===
LOGIN_URL = "https://damadam.pk/login/"
ONLINE_USERS_URL = "https://damadam.pk/online_kon/"

# Get credentials from environment variables (GitHub Secrets)
USERNAME = os.getenv('DAMADAM_USERNAME')
PASSWORD = os.getenv('DAMADAM_PASSWORD')
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

if not all([USERNAME, PASSWORD, SHEET_URL]):
    print("❌ Missing required environment variables!")
    print("Please set: DAMADAM_USERNAME, DAMADAM_PASSWORD, GOOGLE_SHEET_URL")
    sys.exit(1)

# GitHub Actions optimized delays
MIN_DELAY = 0.8
MAX_DELAY = 1.5
LOGIN_DELAY = 3
PAGE_LOAD_TIMEOUT = 10

# === LOGGING ===
def log_msg(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": Fore.WHITE, "SUCCESS": Fore.GREEN, "WARNING": Fore.YELLOW, "ERROR": Fore.RED}
    color = colors.get(level, Fore.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")

# === STATS TRACKING ===
class ScraperStats:
    def __init__(self):
        self.start_time = datetime.now()
        self.total = self.current = self.success = self.errors = 0
        self.exported = self.updated = 0
    
    def show_summary(self):
        elapsed = str(datetime.now() - self.start_time).split('.')[0]
        print(f"\n{Fore.MAGENTA}📊 FINAL SUMMARY:")
        print(f"⏱️  Total Time: {elapsed}")
        print(f"👥 Users Found: {self.total}")
        print(f"✅ Successfully Scraped: {self.success}")
        print(f"❌ Errors: {self.errors}")
        print(f"📊 New Exports: {self.exported}")
        print(f"🔄 Updated Profiles: {self.updated}{Style.RESET_ALL}")
        print("-" * 50)

stats = ScraperStats()

# === GITHUB ACTIONS OPTIMIZED BROWSER ===
def setup_github_browser():
    """Browser setup optimized for GitHub Actions environment"""
    try:
        log_msg("🚀 Setting up browser for GitHub Actions...")
        
        options = webdriver.ChromeOptions()
        
        # GitHub Actions specific options
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--window-size=1920,1080")
        
        # Performance optimizations
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        
        # Remove automation indicators
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--log-level=3")
        
        # Setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        
        # Anti-detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        log_msg("✅ Browser ready for GitHub Actions", "SUCCESS")
        return driver
        
    except Exception as e:
        log_msg(f"❌ Browser setup failed: {e}", "ERROR")
        return None

# === AUTHENTICATION ===
def login_to_damadam(driver):
    """Login to DamaDam"""
    try:
        log_msg("🔐 Logging in to DamaDam...")
        driver.get(LOGIN_URL)
        
        # Wait for login form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "nick"))
        )
        
        # Enter credentials
        driver.find_element(By.ID, "nick").send_keys(USERNAME)
        driver.find_element(By.ID, "pass").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "form button").click()
        
        # Wait for login to complete
        time.sleep(LOGIN_DELAY)
        
        # Check if login successful
        if "login" not in driver.current_url.lower():
            log_msg("✅ Login successful", "SUCCESS")
            return True
        else:
            log_msg("❌ Login failed - still on login page", "ERROR")
            return False
            
    except Exception as e:
        log_msg(f"❌ Login error: {e}", "ERROR")
        return False

# === USER FETCHING ===
def get_online_users(driver):
    """Get list of online users"""
    try:
        log_msg("👥 Fetching online users...")
        driver.get(ONLINE_USERS_URL)
        
        # Wait for user list to load
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li bdi"))
        )
        
        # Extract unique usernames
        users = list({elem.text.strip() 
                     for elem in driver.find_elements(By.CSS_SELECTOR, "li bdi") 
                     if elem.text.strip()})
        
        log_msg(f"✅ Found {len(users)} online users", "SUCCESS")
        return users
        
    except Exception as e:
        log_msg(f"❌ Failed to get users: {e}", "ERROR")
        return []

# === PROFILE SCRAPING ===
def scrape_profile(driver, nickname):
    """Scrape individual user profile"""
    url = f"https://damadam.pk/users/{nickname}/"
    try:
        driver.get(url)
        
        # Wait for profile to load
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.cxl.clb.lsp"))
        )
        
        now = datetime.now()
        data = {
            'DATE': now.strftime("%d-%b-%Y"),
            'TIME': now.strftime("%I:%M %p"),
            'NICKNAME': nickname,
            'TAGS': '',
            'CITY': '',
            'GENDER': '',
            'MARRIED': '',
            'AGE': '',
            'JOINED': '',
            'FOLLOWERS': '',
            'POSTS': '',
            'PLINK': url,
            'PIMAGE': '',
            'INTRO': ''
        }
        
        # Extract intro
        try: 
            intro_elem = driver.find_element(By.CSS_SELECTOR, ".ow span.nos")
            data['INTRO'] = clean_text(intro_elem.text)
        except: 
            pass
            
        # Extract profile fields
        fields_mapping = {
            'City:': 'CITY',
            'Gender:': 'GENDER', 
            'Married:': 'MARRIED',
            'Age:': 'AGE',
            'Joined:': 'JOINED'
        }
        
        for field_text, key in fields_mapping.items():
            try:
                xpath = f"//b[contains(text(), '{field_text}')]/following-sibling::span[1]"
                element = driver.find_element(By.XPATH, xpath)
                value = element.text
                
                if key == "JOINED":
                    data[key] = extract_numbers(value)
                else:
                    data[key] = clean_text(value)
            except: 
                pass
                
        # Extract followers
        try: 
            followers_elem = driver.find_element(By.CSS_SELECTOR, "span.cl.sp.clb")
            followers_match = re.search(r'(\d+)', followers_elem.text)
            if followers_match:
                data['FOLLOWERS'] = followers_match.group(1)
        except: 
            pass
            
        # Extract posts count
        try: 
            posts_elem = driver.find_element(By.CSS_SELECTOR, "a[href*='/profile/public/'] button div:first-child")
            data['POSTS'] = clean_text(posts_elem.text)
        except: 
            pass
            
        # Extract profile image
        try: 
            img_elem = driver.find_element(By.CSS_SELECTOR, "img[src*='avatar-imgs']")
            data['PIMAGE'] = img_elem.get_attribute('src')
        except: 
            pass
            
        return data
        
    except Exception as e:
        log_msg(f"❌ Failed to scrape {nickname}: {e}", "ERROR")
        return None

# === UTILITY FUNCTIONS ===
def clean_text(text):
    """Clean and normalize text"""
    if not text: 
        return ""
    text = str(text).strip().replace('\xa0', ' ').replace('+', '')
    if text.lower() in ['not set', 'no set', 'no city']: 
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def extract_numbers(text):
    """Extract numbers from text"""
    if not text: 
        return ""
    numbers = re.findall(r'\d+', str(text))
    return ', '.join(numbers) if numbers else clean_text(text)

# === GOOGLE SHEETS EXPORT ===
def export_to_google_sheets(profiles_batch):
    """Export profiles to Google Sheets with duplicate handling"""
    if not profiles_batch:
        return False
        
    try:
        log_msg(f"📊 Exporting {len(profiles_batch)} profiles to Google Sheets...", "INFO")
        
        # Setup Google Sheets connection using service account JSON from environment
        google_creds = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not google_creds:
            log_msg("❌ Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable", "ERROR")
            return False
            
        # Parse the JSON credentials
        creds_dict = json.loads(google_creds)
        
        # Setup Google Sheets API
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        workbook = client.open_by_url(SHEET_URL)
        worksheet = workbook.sheet1
        
        # Set up headers if sheet is empty
        headers = ["DATE","TIME","NICKNAME","TAGS","CITY","GENDER","MARRIED","AGE",
                   "JOINED","FOLLOWERS","POSTS","PLINK","PIMAGE","INTRO","SCOUNT"]
        
        existing_data = worksheet.get_all_values()
        if not existing_data or not existing_data[0]: 
            worksheet.append_row(headers)
            log_msg("✅ Headers added to Google Sheet", "SUCCESS")
            existing_nicks = []
        else:
            # Get existing nicknames (column 3, skip header)
            existing_nicks = [row[2] for row in existing_data[1:] if len(row) > 2]
        
        exported_count = 0
        updated_count = 0
        
        for profile in profiles_batch:
            nickname = profile.get("NICKNAME","")
            if not nickname: 
                continue
            
            # Prepare row data
            row = [
                profile.get("DATE",""),
                profile.get("TIME",""),
                nickname,
                "",  # TAGS (empty)
                profile.get("CITY",""),
                profile.get("GENDER",""),
                profile.get("MARRIED",""),
                profile.get("AGE",""),
                profile.get("JOINED",""),
                profile.get("FOLLOWERS",""),
                profile.get("POSTS",""),
                profile.get("PLINK",""),
                profile.get("PIMAGE",""),
                clean_text(profile.get("INTRO","")),
                "1"  # Initial seen count
            ]
            
            # Check if nickname already exists
            if nickname in existing_nicks:
                # Update seen count for existing profile
                row_index = existing_nicks.index(nickname) + 2  # +2 for header and 0-based index
                try:
                    current_count = worksheet.cell(row_index, 15).value or "0"
                    new_count = str(int(current_count) + 1)
                    worksheet.update_cell(row_index, 15, new_count)
                    updated_count += 1
                    stats.updated += 1
                    log_msg(f"🔄 Updated {nickname} (seen {new_count} times)", "INFO")
                except Exception as e:
                    log_msg(f"❌ Failed to update {nickname}: {e}", "ERROR")
            else:
                # Add new profile
                try:
                    worksheet.append_row(row)
                    existing_nicks.append(nickname)
                    exported_count += 1
                    stats.exported += 1
                except Exception as e:
                    log_msg(f"❌ Failed to add {nickname}: {e}", "ERROR")
        
        log_msg(f"✅ Google Sheets export complete: {exported_count} new, {updated_count} updated", "SUCCESS")
        return True
        
    except Exception as e:
        log_msg(f"❌ Google Sheets export failed: {e}", "ERROR")
        return False

# === MAIN EXECUTION ===
def main():
    """Main execution function"""
    log_msg("🚀 Starting DamaDam Profile Scraper", "INFO")
    
    # Setup browser
    driver = setup_github_browser()
    if not driver:
        log_msg("❌ Failed to setup browser", "ERROR")
        return
    
    try:
        # Login
        if not login_to_damadam(driver):
            log_msg("❌ Authentication failed", "ERROR")
            return
        
        # Get online users
        users = get_online_users(driver)
        if not users:
            log_msg("❌ No online users found", "ERROR")
            return
        
        stats.total = len(users)
        scraped_profiles = []
        
        # Scrape profiles
        for i, nickname in enumerate(users, 1):
            stats.current = i
            
            log_msg(f"🔍 Scraping {nickname} ({i}/{stats.total})", "INFO")
            profile = scrape_profile(driver, nickname)
            
            if profile:
                scraped_profiles.append(profile)
                stats.success += 1
                
                # Export in batches of 5
                if len(scraped_profiles) % 5 == 0:
                    export_to_google_sheets(scraped_profiles[-5:])
                    
            else:
                stats.errors += 1
            
            # Random delay to avoid being blocked
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        # Export remaining profiles
        remaining = len(scraped_profiles) % 5
        if remaining > 0:
            export_to_google_sheets(scraped_profiles[-remaining:])
        
        # Final summary
        stats.show_summary()
        
    except Exception as e:
        log_msg(f"❌ Execution error: {e}", "ERROR")
    finally:
        driver.quit()
        log_msg("🏁 Scraper completed", "INFO")

if __name__ == "__main__":
    main()