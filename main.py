#!/usr/bin/env python3
"""
DamaDam Profile Scraper - OPTIMIZED VERSION
GitHub Actions ready with Tags integration and smart updates
"""

import os
import sys
import time
import json
import random
import re
from datetime import datetime

print("🚀 Starting DamaDam Scraper (Optimized Version)...")

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

# === CONFIGURATION ===
LOGIN_URL = "https://damadam.pk/login/"
ONLINE_USERS_URL = "https://damadam.pk/online_kon/"

# Environment variables
USERNAME = os.getenv('DAMADAM_USERNAME')
PASSWORD = os.getenv('DAMADAM_PASSWORD')
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

if not all([USERNAME, PASSWORD, SHEET_URL]):
    print("❌ Missing required environment variables!")
    print("Required: DAMADAM_USERNAME, DAMADAM_PASSWORD, GOOGLE_SHEET_URL")
    sys.exit(1)

# Optimized delays
MIN_DELAY = 1.0
MAX_DELAY = 2.0
LOGIN_DELAY = 4
PAGE_LOAD_TIMEOUT = 8

# Tags configuration
TAGS_CONFIG = {
    'Following': '🔗 Following',
    'Followers': '⭐ Followers', 
    'Bookmark': '🔖 Bookmark',
    'Pending': '⏳ Pending'
}

HIGHLIGHT_COLOR = {
    "red": 1.0,
    "green": 0.9,
    "blue": 0.6
}  # Light mustard color

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
        self.new_profiles = self.updated_profiles = 0
        self.tags_processed = 0
    
    def show_summary(self):
        elapsed = str(datetime.now() - self.start_time).split('.')[0]
        print(f"\n{Fore.MAGENTA}📊 FINAL SUMMARY:")
        print(f"⏱️  Total Time: {elapsed}")
        print(f"🎯 Target Users: {self.total}")
        print(f"✅ Successfully Scraped: {self.success}")
        print(f"❌ Errors: {self.errors}")
        print(f"🆕 New Profiles: {self.new_profiles}")
        print(f"🔄 Updated Profiles: {self.updated_profiles}")
        print(f"🏷️  Tags Processed: {self.tags_processed}")
        
        # Target completion stats
        if self.total > 0:
            completion_rate = (self.success / self.total * 100)
            remaining = self.total - self.success
            print(f"📈 Completion Rate: {completion_rate:.1f}%")
            print(f"⏳ Remaining: {remaining} users pending")
        
        print(f"{Style.RESET_ALL}")
        print("-" * 50)

stats = ScraperStats()

# === BROWSER SETUP ===
def setup_github_browser():
    """Optimized browser setup for GitHub Actions"""
    try:
        log_msg("🚀 Setting up browser for GitHub Actions...")
        
        options = webdriver.ChromeOptions()
        
        # GitHub Actions optimizations
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Performance optimizations
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--log-level=3")
        
        # Try system ChromeDriver first (GitHub Actions pre-installed)
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            # Fallback to ChromeDriverManager
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        
        # Anti-detection scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        
        log_msg("✅ Browser ready", "SUCCESS")
        return driver
        
    except Exception as e:
        log_msg(f"❌ Browser setup failed: {e}", "ERROR")
        return None

# === AUTHENTICATION ===
def login_to_damadam(driver):
    """Enhanced login with comprehensive debugging and multiple strategies"""
    try:
        log_msg("🔐 Logging in to DamaDam...")
        driver.get(LOGIN_URL)
        
        # Wait for page to load completely
        time.sleep(3)
        
        # Debug: Check what page we're on
        current_url = driver.current_url
        page_title = driver.title
        log_msg(f"📍 Current URL: {current_url}", "INFO")
        log_msg(f"📄 Page title: {page_title}", "INFO")
        
        # Try multiple selectors for login form
        login_selectors = [
            {"nick": "#nick", "pass": "#pass", "button": "form button"},
            {"nick": "input[name='nick']", "pass": "input[name='pass']", "button": "button[type='submit']"},
            {"nick": "input[placeholder*='nick']", "pass": "input[type='password']", "button": ".btn"},
            {"nick": "[name='username']", "pass": "[name='password']", "button": "input[type='submit']"},
        ]
        
        form_found = False
        for i, selectors in enumerate(login_selectors):
            try:
                log_msg(f"🔍 Trying login method {i+1}...", "INFO")
                
                # Wait for form elements
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors["nick"]))
                )
                
                nick_field = driver.find_element(By.CSS_SELECTOR, selectors["nick"])
                pass_field = driver.find_element(By.CSS_SELECTOR, selectors["pass"])
                submit_btn = driver.find_element(By.CSS_SELECTOR, selectors["button"])
                
                log_msg(f"✅ Found login form with method {i+1}", "SUCCESS")
                
                # Clear and fill fields
                nick_field.clear()
                time.sleep(0.5)
                nick_field.send_keys(USERNAME)
                
                pass_field.clear()
                time.sleep(0.5)
                pass_field.send_keys(PASSWORD)
                
                # Debug: Check field values
                nick_value = nick_field.get_attribute('value')
                pass_length = len(pass_field.get_attribute('value'))
                log_msg(f"📝 Username filled: {nick_value[:3]}***", "INFO")
                log_msg(f"📝 Password filled: {pass_length} characters", "INFO")
                
                # Submit form
                log_msg("🚀 Submitting login form...", "INFO")
                submit_btn.click()
                form_found = True
                break
                
            except Exception as e:
                log_msg(f"⚠️ Login method {i+1} failed: {e}", "WARNING")
                continue
        
        if not form_found:
            log_msg("❌ No login form found with any method", "ERROR")
            # Debug: Save page source for analysis
            try:
                with open("login_page_debug.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                log_msg("🔍 Login page saved as login_page_debug.html for analysis", "INFO")
            except:
                pass
            return False
        
        # Wait for login to process
        log_msg("⏳ Waiting for login to process...", "INFO")
        time.sleep(LOGIN_DELAY)
        
        # Check login success with multiple indicators
        current_url_after = driver.current_url
        log_msg(f"📍 URL after login: {current_url_after}", "INFO")
        
        # Multiple success checks
        success_indicators = [
            lambda: "login" not in driver.current_url.lower(),
            lambda: "dashboard" in driver.current_url.lower() or "profile" in driver.current_url.lower(),
            lambda: any(driver.find_elements(By.CSS_SELECTOR, selector) for selector in [
                "[href*='logout']", "[href*='profile']", ".user-menu", ".logout"
            ]),
            lambda: not any(driver.find_elements(By.CSS_SELECTOR, selector) for selector in [
                "#nick", "input[name='nick']", ".login-form"
            ])
        ]
        
        login_success = False
        for i, check in enumerate(success_indicators):
            try:
                if check():
                    log_msg(f"✅ Login success indicator {i+1} passed", "SUCCESS")
                    login_success = True
                    break
            except Exception as e:
                log_msg(f"⚠️ Success check {i+1} failed: {e}", "WARNING")
        
        if login_success:
            log_msg("✅ Login successful!", "SUCCESS")
            return True
        else:
            # Check for error messages
            error_selectors = [".error", ".alert", "[class*='error']", "[class*='alert']"]
            for selector in error_selectors:
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in error_elements:
                        if elem.text.strip():
                            log_msg(f"🚨 Error message: {elem.text.strip()}", "ERROR")
                except:
                    pass
            
            log_msg("❌ Login failed - no success indicators found", "ERROR")
            
            # Debug: Save post-login page
            try:
                with open("post_login_debug.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                log_msg("🔍 Post-login page saved as post_login_debug.html", "INFO")
            except:
                pass
                
            return False
            
    except Exception as e:
        log_msg(f"❌ Login error: {e}", "ERROR")
        try:
            with open("login_error_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            log_msg("🔍 Error page saved as login_error_debug.html", "INFO")
        except:
            pass
        return False

# === TARGET USERS MANAGEMENT ===
def get_target_users(client, sheet_url):
    """Get target users from Target sheet"""
    try:
        log_msg("🎯 Loading target users from Target sheet...")
        workbook = client.open_by_url(sheet_url)
        
        # Try to access Target sheet
        try:
            target_sheet = workbook.worksheet("Target")
        except:
            log_msg("❌ Target sheet not found! Please create 'Target' sheet with columns: USERNAME | STATUS | LAST_SCRAPED | NOTES", "ERROR")
            return []
        
        # Get all values from Target sheet
        target_data = target_sheet.get_all_values()
        if not target_data or len(target_data) < 2:
            log_msg("⚠️ Target sheet is empty or has no data rows", "WARNING")
            return []
        
        headers = target_data[0]
        if len(headers) < 2 or 'USERNAME' not in headers[0].upper() or 'STATUS' not in headers[1].upper():
            log_msg("❌ Target sheet headers incorrect. Expected: USERNAME | STATUS | LAST_SCRAPED | NOTES", "ERROR")
            return []
        
        # Extract pending users
        pending_users = []
        for i, row in enumerate(target_data[1:], 2):  # Start from row 2
            if len(row) >= 2:
                username = row[0].strip()
                status = row[1].strip().upper()
                
                if username and status == 'PENDING':
                    pending_users.append({
                        'username': username,
                        'row_index': i,
                        'status': status
                    })
        
        log_msg(f"✅ Found {len(pending_users)} pending users to scrape", "SUCCESS")
        return pending_users
        
    except Exception as e:
        log_msg(f"❌ Failed to load target users: {e}", "ERROR")
        return []

def update_target_status(client, sheet_url, row_index, status, notes=""):
    """Update status of a target user"""
    try:
        workbook = client.open_by_url(sheet_url)
        target_sheet = workbook.worksheet("Target")
        
        # Update status (column B)
        target_sheet.update_cell(row_index, 2, status)
        
        # Update last scraped date (column C) if completed
        if status.upper() == 'COMPLETED':
            from datetime import datetime
            target_sheet.update_cell(row_index, 3, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # Update notes (column D) if provided
        if notes:
            target_sheet.update_cell(row_index, 4, notes)
            
        log_msg(f"✅ Updated target status: {status}", "SUCCESS")
        return True
        
    except Exception as e:
        log_msg(f"❌ Failed to update target status: {e}", "ERROR")
        return False

# === PROFILE SCRAPING ===
def scrape_profile(driver, nickname):
    """Enhanced profile scraping with better data extraction"""
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
            'TAGS': '',  # Will be populated later
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
        
        # Extract intro with multiple selectors
        intro_selectors = [".ow span.nos", ".ow .nos", "span.nos"]
        for selector in intro_selectors:
            try:
                intro_elem = driver.find_element(By.CSS_SELECTOR, selector)
                if intro_elem.text.strip():
                    data['INTRO'] = clean_text(intro_elem.text)
                    break
            except:
                continue
            
        # Extract profile fields with enhanced mapping
        fields_mapping = {
            'City:': 'CITY',
            'Gender:': 'GENDER', 
            'Married:': 'MARRIED',
            'Age:': 'AGE',
            'Joined:': 'JOINED'
        }
        
        for field_text, key in fields_mapping.items():
            try:
                # Try multiple XPath patterns
                xpath_patterns = [
                    f"//b[contains(text(), '{field_text}')]/following-sibling::span[1]",
                    f"//strong[contains(text(), '{field_text}')]/following-sibling::span[1]",
                    f"//*[contains(text(), '{field_text}')]/following-sibling::span[1]"
                ]
                
                for xpath in xpath_patterns:
                    try:
                        element = driver.find_element(By.XPATH, xpath)
                        value = element.text.strip()
                        if value:
                            if key == "JOINED":
                                data[key] = extract_numbers(value)
                            else:
                                data[key] = clean_text(value)
                            break
                    except:
                        continue
            except:
                pass
                
        # Extract followers with multiple selectors
        follower_selectors = ["span.cl.sp.clb", ".cl.sp.clb", "span[class*='cl'][class*='sp']"]
        for selector in follower_selectors:
            try:
                followers_elem = driver.find_element(By.CSS_SELECTOR, selector)
                followers_match = re.search(r'(\d+)', followers_elem.text)
                if followers_match:
                    data['FOLLOWERS'] = followers_match.group(1)
                    break
            except:
                continue
            
        # Extract posts count with multiple selectors
        posts_selectors = [
            "a[href*='/profile/public/'] button div:first-child",
            "a[href*='profile'] button div",
            "button div:first-child"
        ]
        for selector in posts_selectors:
            try:
                posts_elem = driver.find_element(By.CSS_SELECTOR, selector)
                posts_text = clean_text(posts_elem.text)
                if posts_text and posts_text.isdigit():
                    data['POSTS'] = posts_text
                    break
            except:
                continue
            
        # Extract profile image
        img_selectors = ["img[src*='avatar-imgs']", "img[src*='avatar']", ".profile-img img"]
        for selector in img_selectors:
            try:
                img_elem = driver.find_element(By.CSS_SELECTOR, selector)
                data['PIMAGE'] = img_elem.get_attribute('src')
                break
            except:
                continue
            
        return data
        
    except Exception as e:
        log_msg(f"❌ Failed to scrape {nickname}: {e}", "ERROR")
        return None

# === UTILITY FUNCTIONS ===
def clean_text(text):
    """Enhanced text cleaning"""
    if not text: 
        return ""
    text = str(text).strip().replace('\xa0', ' ').replace('+', '').replace('\n', ' ')
    
    # Remove common placeholder texts
    placeholder_texts = ['not set', 'no set', 'no city', 'none', 'n/a', 'null']
    if text.lower() in placeholder_texts: 
        return ""
    
    return re.sub(r'\s+', ' ', text).strip()

def extract_numbers(text):
    """Extract numbers from text with better formatting"""
    if not text: 
        return ""
    numbers = re.findall(r'\d+', str(text))
    return ', '.join(numbers) if numbers else clean_text(text)

# === GOOGLE SHEETS OPERATIONS ===
def get_google_sheets_client():
    """Setup Google Sheets client"""
    try:
        google_creds = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not google_creds:
            raise Exception("Missing GOOGLE_SERVICE_ACCOUNT_JSON")
            
        creds_dict = json.loads(google_creds)
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        return client
    except Exception as e:
        log_msg(f"❌ Failed to setup Google Sheets client: {e}", "ERROR")
        return None

def get_tags_mapping(client, sheet_url):
    """Get tags mapping from Tags sheet"""
    try:
        log_msg("🏷️ Loading tags mapping...")
        workbook = client.open_by_url(sheet_url)
        
        # Try to access Tags sheet
        try:
            tags_sheet = workbook.worksheet("Tags")
        except:
            log_msg("⚠️ Tags sheet not found, skipping tags", "WARNING")
            return {}
        
        # Get all values from Tags sheet
        tags_data = tags_sheet.get_all_values()
        if not tags_data:
            return {}
        
        tags_mapping = {}
        headers = tags_data[0] if tags_data else []
        
        # Process each column
        for col_index, header in enumerate(headers):
            if header.strip():
                tag_icon = TAGS_CONFIG.get(header.strip(), f"📌 {header.strip()}")
                
                # Get all nicknames in this column (skip header)
                for row in tags_data[1:]:
                    if col_index < len(row) and row[col_index].strip():
                        nickname = row[col_index].strip()
                        if nickname not in tags_mapping:
                            tags_mapping[nickname] = []
                        tags_mapping[nickname].append(tag_icon)
        
        stats.tags_processed = len(tags_mapping)
        log_msg(f"✅ Loaded tags for {len(tags_mapping)} users", "SUCCESS")
        return tags_mapping
        
    except Exception as e:
        log_msg(f"❌ Failed to load tags: {e}", "ERROR")
        return {}

def get_tags_for_nickname(nickname, tags_mapping):
    """Get tags string for a nickname"""
    if not tags_mapping or nickname not in tags_mapping:
        return ""
    
    tags = tags_mapping[nickname]
    return ", ".join(tags) if tags else ""

def export_to_google_sheets(profiles_batch, tags_mapping, target_updates=None):
    """Enhanced Google Sheets export with smart updates and target status tracking"""
    if not profiles_batch and not target_updates:
        return False
        
    try:
        log_msg(f"📊 Processing Google Sheets updates...", "INFO")
        
        client = get_google_sheets_client()
        if not client:
            return False
            
        workbook = client.open_by_url(SHEET_URL)
        worksheet = workbook.sheet1
        
        # Handle target status updates first
        if target_updates:
            try:
                target_sheet = workbook.worksheet("Target")
                for update in target_updates:
                    row_idx = update['row_index']
                    status = update['status']
                    notes = update.get('notes', '')
                    
                    # Update status column (B)
                    target_sheet.update_cell(row_idx, 2, status)
                    
                    # Update last scraped (C) if completed
                    if status.upper() == 'COMPLETED':
                        from datetime import datetime
                        target_sheet.update_cell(row_idx, 3, datetime.now().strftime("%Y-%m-%d %H:%M"))
                    
                    # Update notes (D) if provided
                    if notes:
                        target_sheet.update_cell(row_idx, 4, notes)
                        
                log_msg(f"✅ Updated {len(target_updates)} target statuses", "SUCCESS")
            except Exception as e:
                log_msg(f"⚠️ Failed to update target statuses: {e}", "WARNING")
        
        # Process profile data if available
        if not profiles_batch:
            return True
            
        # Setup headers (removed SCOUNT)
        headers = ["DATE","TIME","NICKNAME","TAGS","CITY","GENDER","MARRIED","AGE",
                   "JOINED","FOLLOWERS","POSTS","PLINK","PIMAGE","INTRO"]
        
        existing_data = worksheet.get_all_values()
        if not existing_data or not existing_data[0]: 
            worksheet.append_row(headers)
            log_msg("✅ Headers added to Google Sheet", "SUCCESS")
            existing_rows = {}
        else:
            # Create mapping of nickname to row data and position
            existing_rows = {}
            for i, row in enumerate(existing_data[1:], 2):  # Skip header, start from row 2
                if len(row) > 2 and row[2].strip():  # Check nickname column
                    existing_rows[row[2].strip()] = {
                        'row_index': i,
                        'data': row
                    }
        
        new_count = 0
        updated_count = 0
        
        for profile in profiles_batch:
            nickname = profile.get("NICKNAME","").strip()
            if not nickname: 
                continue
            
            # Add tags to profile
            profile['TAGS'] = get_tags_for_nickname(nickname, tags_mapping)
            
            # Prepare row data
            row = [
                profile.get("DATE",""),
                profile.get("TIME",""),
                nickname,
                profile.get("TAGS",""),
                profile.get("CITY",""),
                profile.get("GENDER",""),
                profile.get("MARRIED",""),
                profile.get("AGE",""),
                profile.get("JOINED",""),
                profile.get("FOLLOWERS",""),
                profile.get("POSTS",""),
                profile.get("PLINK",""),
                profile.get("PIMAGE",""),
                clean_text(profile.get("INTRO",""))
            ]
            
            if nickname in existing_rows:
                # Update existing profile
                existing_info = existing_rows[nickname]
                row_index = existing_info['row_index']
                existing_data = existing_info['data']
                
                # Check if update is needed (compare key fields)
                needs_update = False
                key_fields = [4, 5, 6, 7, 8, 9, 10, 13]  # CITY, GENDER, MARRIED, AGE, JOINED, FOLLOWERS, POSTS, INTRO
                
                for field_idx in key_fields:
                    existing_value = existing_data[field_idx] if field_idx < len(existing_data) else ""
                    new_value = row[field_idx] if field_idx < len(row) else ""
                    if existing_value != new_value and new_value:  # Only update if new value exists
                        needs_update = True
                        break
                
                # Always update DATE, TIME, and TAGS
                if not needs_update:
                    # Check if tags changed
                    existing_tags = existing_data[3] if len(existing_data) > 3 else ""
                    if existing_tags != row[3]:
                        needs_update = True
                
                if needs_update:
                    try:
                        # Update the row (no highlighting since no one watches)
                        range_name = f'A{row_index}:N{row_index}'
                        worksheet.update(range_name, [row])
                        
                        updated_count += 1
                        stats.updated_profiles += 1
                        log_msg(f"🔄 Updated {nickname}", "INFO")
                        
                    except Exception as e:
                        log_msg(f"❌ Failed to update {nickname}: {e}", "ERROR")
                else:
                    log_msg(f"➡️ {nickname} - No changes needed", "INFO")
            else:
                # Add new profile
                try:
                    worksheet.append_row(row)
                    new_count += 1
                    stats.new_profiles += 1
                    log_msg(f"✅ Added new profile: {nickname}", "SUCCESS")
                except Exception as e:
                    log_msg(f"❌ Failed to add {nickname}: {e}", "ERROR")
        
        log_msg(f"📊 Export complete: {new_count} new, {updated_count} updated", "SUCCESS")
        return True
        
    except Exception as e:
        log_msg(f"❌ Google Sheets export failed: {e}", "ERROR")
        return False

# === MAIN EXECUTION ===
def main():
    """Enhanced main execution with target user processing"""
    log_msg("🚀 Starting DamaDam Profile Scraper (Target Mode)", "INFO")
    
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
        
        # Get Google Sheets client and tags mapping
        client = get_google_sheets_client()
        if not client:
            log_msg("❌ Failed to connect to Google Sheets", "ERROR")
            return
            
        tags_mapping = get_tags_mapping(client, SHEET_URL)
        
        # Get target users instead of online users
        target_users = get_target_users(client, SHEET_URL)
        if not target_users:
            log_msg("❌ No target users found or Target sheet not configured", "ERROR")
            return
        
        stats.total = len(target_users)
        scraped_profiles = []
        target_updates = []
        batch_size = 5  # Smaller batch for more frequent updates
        
        log_msg(f"🎯 Processing {stats.total} target users...", "INFO")
        
        # Scrape target profiles
        for i, target_user in enumerate(target_users, 1):
            stats.current = i
            nickname = target_user['username']
            row_index = target_user['row_index']
            
            log_msg(f"🔍 Scraping target user: {nickname} ({i}/{stats.total})", "INFO")
            
            try:
                profile = scrape_profile(driver, nickname)
                
                if profile:
                    scraped_profiles.append(profile)
                    stats.success += 1
                    
                    # Mark as completed in target updates
                    target_updates.append({
                        'row_index': row_index,
                        'status': 'Completed',
                        'notes': 'Successfully scraped'
                    })
                    
                    log_msg(f"✅ Successfully scraped: {nickname}", "SUCCESS")
                    
                else:
                    stats.errors += 1
                    # Mark as failed (keep as Pending for retry)
                    target_updates.append({
                        'row_index': row_index,
                        'status': 'Pending',
                        'notes': 'Scraping failed - will retry'
                    })
                    log_msg(f"❌ Failed to scrape: {nickname}", "ERROR")
                
                # Export in batches with target updates
                if len(scraped_profiles) >= batch_size or len(target_updates) >= batch_size:
                    export_to_google_sheets(scraped_profiles, tags_mapping, target_updates)
                    scraped_profiles = []  # Clear batch
                    target_updates = []   # Clear updates
                    
            except Exception as e:
                stats.errors += 1
                log_msg(f"❌ Error processing {nickname}: {e}", "ERROR")
                
                # Mark as failed
                target_updates.append({
                    'row_index': row_index,
                    'status': 'Pending',
                    'notes': f'Error: {str(e)[:100]}'
                })
            
            # Smart delay to avoid detection
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            time.sleep(delay)
        
        # Export remaining profiles and updates
        if scraped_profiles or target_updates:
            export_to_google_sheets(scraped_profiles, tags_mapping, target_updates)
        
        # Final summary
        stats.show_summary()
        
        # Show target completion status
        completed = stats.success
        total_targets = stats.total
        completion_rate = (completed / total_targets * 100) if total_targets > 0 else 0
        
        log_msg(f"🎯 Target Processing Complete:", "INFO")
        log_msg(f"   Completed: {completed}/{total_targets} ({completion_rate:.1f}%)", "INFO")
        log_msg(f"   Remaining: {total_targets - completed} users still pending", "INFO")
        
    except KeyboardInterrupt:
        log_msg("⏹️ Scraping interrupted by user", "WARNING")
    except Exception as e:
        log_msg(f"❌ Execution error: {e}", "ERROR")
    finally:
        try:
            driver.quit()
        except:
            pass
        log_msg("🏁 Scraper completed", "INFO")

if __name__ == "__main__":
    main()
