#!/usr/bin/env python3
"""
DamaDam Profile Scraper - SIMPLIFIED GITHUB ACTIONS VERSION
More reliable ChromeDriver setup for cloud execution
"""

import os
import sys
import time
import json
import random
import re
import subprocess
from datetime import datetime

print("🚀 Starting DamaDam Scraper (Simplified GitHub Actions Version)...")

# Check and install packages
def install_requirements():
    packages = [
        "selenium==4.15.2",
        "gspread==5.12.0", 
        "oauth2client==4.1.3",
        "colorama==0.4.6"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        except:
            print(f"⚠️ Could not install {package}")

# Install requirements first
install_requirements()

# Now import packages
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    print("✅ Selenium ready")
except ImportError as e:
    print(f"❌ Selenium import failed: {e}")
    sys.exit(1)

try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    print("✅ Colors ready")
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = WHITE = MAGENTA = BLUE = ""
    class Style:
        RESET_ALL = ""

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    print("✅ Google Sheets ready")
except ImportError as e:
    print(f"❌ Google Sheets import failed: {e}")
    sys.exit(1)

# === CONFIGURATION ===
LOGIN_URL = "https://damadam.pk/login/"
ONLINE_USERS_URL = "https://damadam.pk/online_kon/"

USERNAME = os.getenv('DAMADAM_USERNAME')
PASSWORD = os.getenv('DAMADAM_PASSWORD')
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

if not all([USERNAME, PASSWORD, SHEET_URL]):
    print("❌ Missing environment variables!")
    sys.exit(1)

# Optimized delays for GitHub Actions
MIN_DELAY = 1.5
MAX_DELAY = 2.5
LOGIN_DELAY = 5
PAGE_LOAD_TIMEOUT = 20

# === LOGGING ===
def log_msg(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": Fore.WHITE, "SUCCESS": Fore.GREEN, "WARNING": Fore.YELLOW, "ERROR": Fore.RED}
    color = colors.get(level, Fore.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")

# === STATS ===
class ScraperStats:
    def __init__(self):
        self.start_time = datetime.now()
        self.total = self.success = self.errors = self.exported = self.updated = 0

stats = ScraperStats()

# === SIMPLIFIED BROWSER SETUP ===
def setup_chrome_browser():
    """Simplified and more reliable browser setup for GitHub Actions"""
    try:
        log_msg("🚀 Setting up Chrome browser...", "INFO")
        
        # Chrome options optimized for GitHub Actions
        options = webdriver.ChromeOptions()
        
        # Essential headless options
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Stability options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Faster loading
        options.add_argument("--disable-javascript")  # We don't need JS for scraping
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        
        # Memory optimization
        options.add_argument("--memory-pressure-off")
        options.add_argument("--aggressive-cache-discard")
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--log-level=3")  # Suppress logs
        
        # Try different ChromeDriver methods
        driver = None
        
        # Method 1: Use system ChromeDriver (usually available in GitHub Actions)
        try:
            log_msg("🔧 Attempting system ChromeDriver...", "INFO")
            # Check if chromedriver is in PATH
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            if result.returncode == 0:
                chromedriver_path = result.stdout.strip()
                log_msg(f"Found system ChromeDriver at: {chromedriver_path}", "INFO")
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                log_msg("No system ChromeDriver found", "WARNING")
        except Exception as e:
            log_msg(f"System ChromeDriver failed: {e}", "WARNING")
        
        # Method 2: Try without explicit service (let Selenium find it)
        if not driver:
            try:
                log_msg("🔧 Attempting automatic ChromeDriver detection...", "INFO")
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                log_msg(f"Automatic detection failed: {e}", "WARNING")
        
        # Method 3: Download ChromeDriver manually
        if not driver:
            try:
                log_msg("🔧 Downloading ChromeDriver...", "INFO")
                # Simple ChromeDriver download
                chrome_version = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
                log_msg(f"Chrome version: {chrome_version.stdout.strip()}", "INFO")
                
                # Use webdriver-manager as fallback
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                log_msg(f"ChromeDriver download failed: {e}", "ERROR")
                return None
        
        if not driver:
            log_msg("❌ All ChromeDriver methods failed", "ERROR")
            return None
        
        # Set timeouts
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(5)
        
        # Anti-detection scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        log_msg("✅ Chrome browser ready", "SUCCESS")
        return driver
        
    except Exception as e:
        log_msg(f"❌ Browser setup failed: {e}", "ERROR")
        return None

# === AUTHENTICATION ===
def login_to_site(driver):
    """Login to DamaDam"""
    try:
        log_msg("🔐 Logging in to DamaDam...", "INFO")
        driver.get(LOGIN_URL)
        
        # Wait for login form
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "nick"))
        )
        
        # Enter credentials
        nick_field = driver.find_element(By.ID, "nick")
        pass_field = driver.find_element(By.ID, "pass")
        login_button = driver.find_element(By.CSS_SELECTOR, "form button")
        
        nick_field.clear()
        nick_field.send_keys(USERNAME)
        pass_field.clear() 
        pass_field.send_keys(PASSWORD)
        login_button.click()
        
        # Wait for login to complete
        time.sleep(LOGIN_DELAY)
        
        # Check if login successful
        if "login" not in driver.current_url.lower():
            log_msg("✅ Login successful", "SUCCESS")
            return True
        else:
            log_msg("❌ Login failed - check credentials", "ERROR")
            return False
            
    except Exception as e:
        log_msg(f"❌ Login error: {e}", "ERROR")
        return False

# === USER FETCHING ===
def get_online_users(driver):
    """Get online users list"""
    try:
        log_msg("👥 Fetching online users...", "INFO")
        driver.get(ONLINE_USERS_URL)
        
        # Wait for users list
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li bdi"))
        )
        
        # Extract usernames
        user_elements = driver.find_elements(By.CSS_SELECTOR, "li bdi")
        users = []
        
        for elem in user_elements:
            username = elem.text.strip()
            if username and username not in users:
                users.append(username)
        
        log_msg(f"✅ Found {len(users)} online users", "SUCCESS")
        return users
        
    except Exception as e:
        log_msg(f"❌ Failed to get users: {e}", "ERROR")
        return []

# === PROFILE SCRAPING ===
def scrape_user_profile(driver, nickname):
    """Scrape individual profile"""
    url = f"https://damadam.pk/users/{nickname}/"
    
    try:
        driver.get(url)
        
        # Wait for profile page
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        
        # Basic data structure
        now = datetime.now()
        profile_data = {
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
        
        # Extract intro/bio
        try:
            intro_elem = driver.find_element(By.CSS_SELECTOR, ".ow span.nos")
            profile_data['INTRO'] = clean_text(intro_elem.text)
        except:
            pass
        
        # Extract profile fields
        field_mappings = {
            'City:': 'CITY',
            'Gender:': 'GENDER',
            'Married:': 'MARRIED', 
            'Age:': 'AGE',
            'Joined:': 'JOINED'
        }
        
        for field, key in field_mappings.items():
            try:
                xpath = f"//b[contains(text(), '{field}')]/following-sibling::span[1]"
                elem = driver.find_element(By.XPATH, xpath)
                value = elem.text.strip()
                
                if key == "JOINED":
                    # Extract year numbers
                    numbers = re.findall(r'\d+', value)
                    profile_data[key] = ', '.join(numbers) if numbers else clean_text(value)
                else:
                    profile_data[key] = clean_text(value)
            except:
                pass
        
        # Extract followers
        try:
            followers_elem = driver.find_element(By.CSS_SELECTOR, "span.cl.sp.clb")
            followers_text = followers_elem.text
            match = re.search(r'(\d+)', followers_text)
            if match:
                profile_data['FOLLOWERS'] = match.group(1)
        except:
            pass
        
        # Extract posts count
        try:
            posts_elem = driver.find_element(By.CSS_SELECTOR, "a[href*='/profile/public/'] button div:first-child")
            profile_data['POSTS'] = clean_text(posts_elem.text)
        except:
            pass
        
        # Extract profile image
        try:
            img_elem = driver.find_element(By.CSS_SELECTOR, "img[src*='avatar-imgs']")
            profile_data['PIMAGE'] = img_elem.get_attribute('src')
        except:
            pass
        
        return profile_data
        
    except Exception as e:
        log_msg(f"❌ Failed to scrape {nickname}: {e}", "ERROR")
        return None

# === UTILITY FUNCTIONS ===
def clean_text(text):
    """Clean text data"""
    if not text:
        return ""
    text = str(text).strip().replace('\xa0', ' ').replace('+', '')
    if text.lower() in ['not set', 'no set', 'no city']:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

# === GOOGLE SHEETS EXPORT ===
def export_to_sheets(profiles_list):
    """Export profiles to Google Sheets"""
    if not profiles_list:
        return False
    
    try:
        log_msg(f"📊 Exporting {len(profiles_list)} profiles to Google Sheets...", "INFO")
        
        # Get Google credentials from environment
        google_creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not google_creds_json:
            log_msg("❌ Missing Google credentials", "ERROR")
            return False
        
        # Setup Google Sheets connection
        creds_dict = json.loads(google_creds_json)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        workbook = client.open_by_url(SHEET_URL)
        worksheet = workbook.sheet1
        
        # Setup headers
        headers = ["DATE","TIME","NICKNAME","TAGS","CITY","GENDER","MARRIED","AGE",
                  "JOINED","FOLLOWERS","POSTS","PLINK","PIMAGE","INTRO","SCOUNT"]
        
        # Check if headers exist
        existing_data = worksheet.get_all_values()
        if not existing_data or not existing_data[0]:
            worksheet.append_row(headers)
            existing_nicknames = []
            log_msg("✅ Headers added to sheet", "SUCCESS")
        else:
            # Get existing nicknames (column 3)
            existing_nicknames = [row[2] for row in existing_data[1:] if len(row) > 2]
        
        exported_count = 0
        updated_count = 0
        
        # Process each profile
        for profile in profiles_list:
            nickname = profile.get("NICKNAME", "")
            if not nickname:
                continue
            
            # Prepare row data
            row_data = [
                profile.get("DATE", ""),
                profile.get("TIME", ""),
                nickname,
                "",  # TAGS
                profile.get("CITY", ""),
                profile.get("GENDER", ""),
                profile.get("MARRIED", ""),
                profile.get("AGE", ""),
                profile.get("JOINED", ""),
                profile.get("FOLLOWERS", ""),
                profile.get("POSTS", ""),
                profile.get("PLINK", ""),
                profile.get("PIMAGE", ""),
                clean_text(profile.get("INTRO", "")),
                "1"  # Initial seen count
            ]
            
            # Check for duplicates
            if nickname in existing_nicknames:
                # Update seen count
                try:
                    row_index = existing_nicknames.index(nickname) + 2
                    current_count = worksheet.cell(row_index, 15).value or "0"
                    new_count = str(int(current_count) + 1)
                    worksheet.update_cell(row_index, 15, new_count)
                    updated_count += 1
                    stats.updated += 1
                    log_msg(f"🔄 Updated {nickname} (seen {new_count} times)", "INFO")
                except Exception as e:
                    log_msg(f"Failed to update {nickname}: {e}", "WARNING")
            else:
                # Add new profile
                try:
                    worksheet.append_row(row_data)
                    existing_nicknames.append(nickname)
                    exported_count += 1
                    stats.exported += 1
                except Exception as e:
                    log_msg(f"Failed to add {nickname}: {e}", "WARNING")
        
        log_msg(f"✅ Export complete: {exported_count} new, {updated_count} updated", "SUCCESS")
        return True
        
    except Exception as e:
        log_msg(f"❌ Google Sheets export failed: {e}", "ERROR")
        return False

# === MAIN EXECUTION ===
def main():
    """Main execution function"""
    log_msg("🚀 Starting DamaDam Profile Scraper", "INFO")
    
    # Setup browser
    driver = setup_chrome_browser()
    if not driver:
        log_msg("❌ Cannot continue without browser", "ERROR")
        return
    
    try:
        # Login to site
        if not login_to_site(driver):
            log_msg("❌ Login failed - stopping execution", "ERROR")
            return
        
        # Get online users
        users = get_online_users(driver)
        if not users:
            log_msg("❌ No online users found", "WARNING")
            return
        
        stats.total = len(users)
        scraped_profiles = []
        
        # Scrape each user profile
        for i, username in enumerate(users, 1):
            log_msg(f"🔍 Scraping {username} ({i}/{stats.total})", "INFO")
            
            profile = scrape_user_profile(driver, username)
            
            if profile:
                scraped_profiles.append(profile)
                stats.success += 1
                
                # Export in batches of 10 for efficiency  
                if len(scraped_profiles) % 10 == 0:
                    export_to_sheets(scraped_profiles[-10:])
            else:
                stats.errors += 1
            
            # Random delay between requests
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        # Export any remaining profiles
        remaining = len(scraped_profiles) % 10
        if remaining > 0:
            export_to_sheets(scraped_profiles[-remaining:])
        
        # Final summary
        elapsed_time = str(datetime.now() - stats.start_time).split('.')[0]
        log_msg(f"🎉 COMPLETED! Time: {elapsed_time}", "SUCCESS")
        log_msg(f"📊 Total: {stats.total} | Success: {stats.success} | Errors: {stats.errors}", "INFO")
        log_msg(f"📈 Exported: {stats.exported} | Updated: {stats.updated}", "INFO")
        
    except Exception as e:
        log_msg(f"❌ Execution error: {e}", "ERROR")
    finally:
        if driver:
            driver.quit()
        log_msg("🏁 Scraper finished", "INFO")

if __name__ == "__main__":
    main()
