#!/usr/bin/env python3
"""
DamaDam Profile Scraper - ENHANCED VERSION with Recent Post Data
GitHub Actions ready with Tags integration and smart updates
"""

import os
import sys
import time
import json
import random
import re
from datetime import datetime, timedelta

print("🚀 Starting DamaDam Scraper (Enhanced with Post Data)...")

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

# Environment variables
USERNAME = os.getenv('DAMADAM_USERNAME')
PASSWORD = os.getenv('DAMADAM_PASSWORD')
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

if not all([USERNAME, PASSWORD, SHEET_URL]):
    print("❌ Missing required environment variables!")
    print("Required: DAMADAM_USERNAME, DAMADAM_PASSWORD, GOOGLE_SHEET_URL")
    sys.exit(1)

# Rate limiting configuration
GOOGLE_API_RATE_LIMIT = {
    'max_requests_per_minute': 50,
    'batch_size': 3,
    'retry_delay': 65,
    'request_delay': 1.2
}

api_requests = []

def track_api_request():
    """Track API requests for rate limiting"""
    now = datetime.now()
    global api_requests
    api_requests = [req_time for req_time in api_requests if (now - req_time).seconds < 60]
    api_requests.append(now)
    if len(api_requests) >= GOOGLE_API_RATE_LIMIT['max_requests_per_minute']:
        log_msg("⏸️ Rate limit approaching, pausing for 65 seconds...", "WARNING")
        time.sleep(GOOGLE_API_RATE_LIMIT['retry_delay'])
        api_requests = []

MIN_DELAY = 1.0
MAX_DELAY = 2.0
LOGIN_DELAY = 4

TAGS_CONFIG = {
    'Following': '🔗 Following',
    'Followers': '⭐ Followers', 
    'Bookmark': '📖 Bookmark',
    'Pending': '⏳ Pending'
}

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
        self.total = self.current = self.success = self.errors = 0
        self.new_profiles = self.updated_profiles = 0
        self.tags_processed = self.posts_scraped = 0
    
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
        print(f"📝 Posts Scraped: {self.posts_scraped}")
        if self.total > 0:
            completion_rate = (self.success / self.total * 100)
            print(f"📈 Completion Rate: {completion_rate:.1f}%")
        print(f"{Style.RESET_ALL}")

stats = ScraperStats()

# === DATE CONVERSION ===
def convert_relative_date_to_absolute(relative_text):
    """Convert '2 months ago' to 'dd-mmm-yy'"""
    if not relative_text:
        return ""
    
    relative_text = relative_text.lower().strip()
    now = datetime.now()
    
    try:
        match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', relative_text)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'second':
                target_date = now - timedelta(seconds=amount)
            elif unit == 'minute':
                target_date = now - timedelta(minutes=amount)
            elif unit == 'hour':
                target_date = now - timedelta(hours=amount)
            elif unit == 'day':
                target_date = now - timedelta(days=amount)
            elif unit == 'week':
                target_date = now - timedelta(weeks=amount)
            elif unit == 'month':
                target_date = now - timedelta(days=amount * 30)
            elif unit == 'year':
                target_date = now - timedelta(days=amount * 365)
            else:
                return relative_text
            
            return target_date.strftime("%d-%b-%y")
        return relative_text
    except:
        return relative_text

def parse_post_timestamp(timestamp_text):
    """Parse post timestamp to 'dd-mmm-yy hh:mm A/P'"""
    if not timestamp_text:
        return "N/A"
    
    timestamp_text = timestamp_text.strip()
    now = datetime.now()
    
    try:
        match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', timestamp_text.lower())
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'second':
                target_date = now - timedelta(seconds=amount)
            elif unit == 'minute':
                target_date = now - timedelta(minutes=amount)
            elif unit == 'hour':
                target_date = now - timedelta(hours=amount)
            elif unit == 'day':
                target_date = now - timedelta(days=amount)
            elif unit == 'week':
                target_date = now - timedelta(weeks=amount)
            elif unit == 'month':
                target_date = now - timedelta(days=amount * 30)
            elif unit == 'year':
                target_date = now - timedelta(days=amount * 365)
            else:
                return timestamp_text
            
            return target_date.strftime("%d-%b-%y %I:%M %p")
        return timestamp_text
    except:
        return timestamp_text

# === BROWSER SETUP ===
def setup_github_browser():
    """Setup browser for GitHub Actions"""
    try:
        log_msg("🚀 Setting up browser...", "INFO")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--log-level=3")
        
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
        except:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        driver.set_page_load_timeout(15)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        log_msg("✅ Browser ready", "SUCCESS")
        return driver
    except Exception as e:
        log_msg(f"❌ Browser setup failed: {e}", "ERROR")
        return None

# === AUTHENTICATION ===
def login_to_damadam(driver):
    """Login to DamaDam"""
    try:
        log_msg("🔐 Logging in...", "INFO")
        driver.get(LOGIN_URL)
        time.sleep(3)
        
        login_selectors = [
            {"nick": "#nick", "pass": "#pass", "button": "form button"},
            {"nick": "input[name='nick']", "pass": "input[name='pass']", "button": "button[type='submit']"}
        ]
        
        for i, sel in enumerate(login_selectors):
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel["nick"])))
                nick_field = driver.find_element(By.CSS_SELECTOR, sel["nick"])
                pass_field = driver.find_element(By.CSS_SELECTOR, sel["pass"])
                submit_btn = driver.find_element(By.CSS_SELECTOR, sel["button"])
                
                nick_field.clear()
                time.sleep(0.5)
                nick_field.send_keys(USERNAME)
                pass_field.clear()
                time.sleep(0.5)
                pass_field.send_keys(PASSWORD)
                submit_btn.click()
                break
            except:
                continue
        
        time.sleep(LOGIN_DELAY)
        
        if "login" not in driver.current_url.lower():
            log_msg("✅ Login successful!", "SUCCESS")
            return True
        else:
            log_msg("❌ Login failed", "ERROR")
            return False
    except Exception as e:
        log_msg(f"❌ Login error: {e}", "ERROR")
        return False

# === TARGET USERS ===
def get_target_users(client, sheet_url):
    """Get target users from Target sheet"""
    try:
        log_msg("🎯 Loading target users...", "INFO")
        workbook = client.open_by_url(sheet_url)
        target_sheet = workbook.worksheet("Target")
        target_data = target_sheet.get_all_values()
        
        if not target_data or len(target_data) < 2:
            log_msg("⚠️ Target sheet empty", "WARNING")
            return []
        
        pending_users = []
        for i, row in enumerate(target_data[1:], 2):
            if len(row) >= 2:
                username = row[0].strip()
                status = row[1].strip().upper()
                if username and status == 'PENDING':
                    pending_users.append({'username': username, 'row_index': i})
        
        log_msg(f"✅ Found {len(pending_users)} pending users", "SUCCESS")
        return pending_users
    except Exception as e:
        log_msg(f"❌ Failed to load targets: {e}", "ERROR")
        return []

# === POST SCRAPING ===
def scrape_recent_post(driver, nickname):
    """Scrape recent post URL from /profile/public/{nickname}"""
    post_url = f"https://damadam.pk/profile/public/{nickname}"
    try:
        log_msg(f"📝 Scraping post for {nickname}...", "INFO")
        driver.get(post_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.mbl.bas-sh")))
        
        recent_post = driver.find_element(By.CSS_SELECTOR, "article.mbl.bas-sh")
        post_data = {'LPOST': '', 'LDATE-TIME': ''}
        
        # Get post URL - Try multiple patterns for text and image posts
        url_selectors = [
            "a[href*='/content/']",           # Image posts: /content/42403588/g/
            "a[href*='/comments/text/']",     # Text posts: /comments/text/42442215/29/
            "a[href*='/comments/image/']",    # Image posts (alternative): /comments/image/42403588/29/
        ]
        
        for sel in url_selectors:
            try:
                link_elem = recent_post.find_element(By.CSS_SELECTOR, sel)
                href = link_elem.get_attribute('href')
                if href:
                    # Extract post ID and construct clean URL
                    if '/content/' in href:
                        # Image post - use as is
                        post_data['LPOST'] = href if href.startswith('http') else f"https://damadam.pk{href}"
                        break
                    elif '/comments/text/' in href:
                        # Text post - extract ID and make clean URL
                        match = re.search(r'/comments/text/(\d+)/', href)
                        if match:
                            post_id = match.group(1)
                            post_data['LPOST'] = f"https://damadam.pk/comments/text/{post_id}/"
                            break
                    elif '/comments/image/' in href:
                        # Image post comment link - extract ID and make clean URL
                        match = re.search(r'/comments/image/(\d+)/', href)
                        if match:
                            post_id = match.group(1)
                            post_data['LPOST'] = f"https://damadam.pk/content/{post_id}/g/"
                            break
            except:
                continue
        
        if not post_data['LPOST']:
            post_data['LPOST'] = "[No Post URL]"
        
        # Get timestamp
        time_selectors = ["time[itemprop='datePublished']", "time"]
        for sel in time_selectors:
            try:
                elem = recent_post.find_element(By.CSS_SELECTOR, sel)
                if elem.text.strip():
                    post_data['LDATE-TIME'] = parse_post_timestamp(elem.text.strip())
                    break
            except:
                continue
        
        if not post_data['LDATE-TIME']:
            post_data['LDATE-TIME'] = "N/A"
        
        stats.posts_scraped += 1
        log_msg(f"✅ Post URL: {post_data['LPOST']}", "SUCCESS")
        return post_data
    except TimeoutException:
        log_msg(f"⏳ No posts for {nickname}", "WARNING")
        return {'LPOST': '[No Posts]', 'LDATE-TIME': 'N/A'}
    except Exception as e:
        log_msg(f"❌ Post scrape failed: {e}", "ERROR")
        return {'LPOST': '[Error]', 'LDATE-TIME': 'N/A'}

# === PROFILE SCRAPING ===
def scrape_profile(driver, nickname):
    """Scrape profile with post data"""
    url = f"https://damadam.pk/users/{nickname}/"
    try:
        driver.get(url)
        WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.cxl.clb.lsp")))
        
        now = datetime.now()
        data = {
            'DATETIME': now.strftime("%d-%b-%y %I:%M %p"),
            'NICKNAME': nickname,
            'TAGS': '',
            'CITY': '',
            'GENDER': '',
            'MARRIED': '',
            'AGE': '',
            'JOINED': '',
            'FOLLOWERS': '',
            'POSTS': '',
            'LPOST': '',
            'LDATE-TIME': '',
            'PLINK': url,
            'PIMAGE': '',
            'INTRO': ''
        }
        
        # Intro
        for sel in [".ow span.nos", ".ow .nos", "span.nos"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                if elem.text.strip():
                    data['INTRO'] = clean_text(elem.text)
                    break
            except:
                pass
        
        # Profile fields
        fields = {'City:': 'CITY', 'Gender:': 'GENDER', 'Married:': 'MARRIED', 'Age:': 'AGE', 'Joined:': 'JOINED'}
        for field_text, key in fields.items():
            try:
                xpath = f"//b[contains(text(), '{field_text}')]/following-sibling::span[1]"
                elem = driver.find_element(By.XPATH, xpath)
                value = elem.text.strip()
                if value:
                    data[key] = convert_relative_date_to_absolute(value) if key == "JOINED" else clean_text(value)
            except:
                pass
        
        # Followers
        for sel in ["span.cl.sp.clb", ".cl.sp.clb"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                match = re.search(r'(\d+)', elem.text)
                if match:
                    data['FOLLOWERS'] = match.group(1)
                    break
            except:
                pass
        
        # Posts count
        for sel in ["a[href*='/profile/public/'] button div:first-child", "a[href*='/profile/public/'] button div"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                match = re.search(r'(\d+)', elem.text)
                if match:
                    data['POSTS'] = match.group(1)
                    break
            except:
                pass
        
        # Profile image
        for sel in ["img[src*='avatar-imgs']", "img[src*='avatar']"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                data['PIMAGE'] = elem.get_attribute('src')
                break
            except:
                pass
        
        # Recent post
        time.sleep(1)
        post_data = scrape_recent_post(driver, nickname)
        data['LPOST'] = post_data['LPOST']
        data['LDATE-TIME'] = post_data['LDATE-TIME']
        
        return data
    except Exception as e:
        log_msg(f"❌ Failed to scrape {nickname}: {e}", "ERROR")
        return None

# === UTILITIES ===
def clean_text(text):
    """Clean text"""
    if not text:
        return ""
    text = str(text).strip().replace('\xa0', ' ').replace('\n', ' ')
    return re.sub(r'\s+', ' ', text).strip()

# === GOOGLE SHEETS ===
def get_google_sheets_client():
    """Setup Google Sheets"""
    try:
        creds_dict = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        log_msg(f"❌ Sheets client failed: {e}", "ERROR")
        return None

def get_tags_mapping(client, sheet_url):
    """Get tags from Tags sheet"""
    try:
        log_msg("🏷️ Loading tags...", "INFO")
        workbook = client.open_by_url(sheet_url)
        tags_sheet = workbook.worksheet("Tags")
        tags_data = tags_sheet.get_all_values()
        
        if not tags_data:
            return {}
        
        tags_mapping = {}
        headers = tags_data[0]
        for col_idx, header in enumerate(headers):
            if header.strip():
                tag_icon = TAGS_CONFIG.get(header.strip(), f"🔌 {header.strip()}")
                for row in tags_data[1:]:
                    if col_idx < len(row) and row[col_idx].strip():
                        nick = row[col_idx].strip()
                        if nick not in tags_mapping:
                            tags_mapping[nick] = []
                        tags_mapping[nick].append(tag_icon)
        
        stats.tags_processed = len(tags_mapping)
        log_msg(f"✅ Loaded {len(tags_mapping)} tags", "SUCCESS")
        return tags_mapping
    except:
        log_msg("⚠️ Tags sheet not found", "WARNING")
        return {}

def get_tags_for_nickname(nickname, tags_mapping):
    """Get tags string"""
    if not tags_mapping or nickname not in tags_mapping:
        return ""
    return ", ".join(tags_mapping[nickname])

def export_to_google_sheets_with_rate_limiting(profiles_batch, tags_mapping, target_updates=None):
    """Export with rate limiting"""
    if not profiles_batch and not target_updates:
        return False
    
    try:
        log_msg("📊 Exporting to Google Sheets...", "INFO")
        client = get_google_sheets_client()
        if not client:
            return False
        
        workbook = client.open_by_url(SHEET_URL)
        
        # Update target statuses
        if target_updates:
            try:
                target_sheet = workbook.worksheet("Target")
                for update in target_updates:
                    try:
                        track_api_request()
                        row_idx = update['row_index']
                        status = update['status']
                        notes = update.get('notes', '')
                        
                        update_range = f'B{row_idx}:D{row_idx}'
                        update_values = [status]
                        update_values.append(datetime.now().strftime("%Y-%m-%d %H:%M") if status.upper() == 'COMPLETED' else '')
                        update_values.append(notes)
                        
                        target_sheet.update(update_range, [update_values])
                        time.sleep(GOOGLE_API_RATE_LIMIT['request_delay'])
                    except Exception as e:
                        if "429" in str(e):
                            time.sleep(65)
                            target_sheet.update(update_range, [update_values])
                log_msg(f"✅ Updated {len(target_updates)} target statuses", "SUCCESS")
            except Exception as e:
                log_msg(f"⚠️ Target update failed: {e}", "WARNING")
        
        if not profiles_batch:
            return True
        
        # Main worksheet
        worksheet = workbook.sheet1
        headers = ["DATETIME","NICKNAME","TAGS","CITY","GENDER","MARRIED","AGE","JOINED","FOLLOWERS","POSTS","LPOST","LDATE-TIME","PLINK","PIMAGE","INTRO"]
        
        track_api_request()
        existing_data = worksheet.get_all_values()
        
        if not existing_data or not existing_data[0]:
            track_api_request()
            worksheet.append_row(headers)
            log_msg("✅ Headers added", "SUCCESS")
            existing_rows = {}
        else:
            existing_rows = {}
            for i, row in enumerate(existing_data[1:], 2):
                if len(row) > 1 and row[1].strip():
                    existing_rows[row[1].strip()] = {'row_index': i, 'data': row}
        
        new_count = updated_count = 0
        
        for profile in profiles_batch:
            try:
                nickname = profile.get("NICKNAME", "").strip()
                if not nickname:
                    continue
                
                profile['TAGS'] = get_tags_for_nickname(nickname, tags_mapping)
                
                row = [
                    profile.get("DATETIME", ""),
                    nickname,
                    profile.get("TAGS", ""),
                    profile.get("CITY", ""),
                    profile.get("GENDER", ""),
                    profile.get("MARRIED", ""),
                    profile.get("AGE", ""),
                    profile.get("JOINED", ""),
                    profile.get("FOLLOWERS", ""),
                    profile.get("POSTS", ""),
                    profile.get("LPOST", ""),
                    profile.get("LDATE-TIME", ""),
                    profile.get("PLINK", ""),
                    profile.get("PIMAGE", ""),
                    clean_text(profile.get("INTRO", ""))
                ]
                
                if nickname in existing_rows:
                    info = existing_rows[nickname]
                    row_index = info['row_index']
                    old_row = info['data']
                    
                    needs_update = False
                    for idx in [3,4,5,6,7,8,9,10,11,14]:
                        old_val = old_row[idx] if idx < len(old_row) else ""
                        new_val = row[idx] if idx < len(row) else ""
                        if old_val != new_val and new_val:
                            needs_update = True
                            break
                    
                    if not needs_update:
                        old_tags = old_row[2] if len(old_row) > 2 else ""
                        if old_tags != row[2]:
                            needs_update = True
                    
                    if needs_update:
                        try:
                            track_api_request()
                            worksheet.update(f'A{row_index}:O{row_index}', [row])
                            updated_count += 1
                            stats.updated_profiles += 1
                            log_msg(f"🔄 Updated {nickname}", "INFO")
                            time.sleep(GOOGLE_API_RATE_LIMIT['request_delay'])
                        except Exception as e:
                            if "429" in str(e):
                                time.sleep(65)
                                worksheet.update(f'A{row_index}:O{row_index}', [row])
                                updated_count += 1
                    else:
                        log_msg(f"➡️ {nickname} - No changes", "INFO")
                else:
                    try:
                        track_api_request()
                        worksheet.append_row(row)
                        new_count += 1
                        stats.new_profiles += 1
                        log_msg(f"✅ Added {nickname}", "SUCCESS")
                        time.sleep(GOOGLE_API_RATE_LIMIT['request_delay'])
                    except Exception as e:
                        if "429" in str(e):
                            time.sleep(65)
                            worksheet.append_row(row)
                            new_count += 1
            except Exception as e:
                log_msg(f"❌ Error processing {nickname}: {e}", "ERROR")
        
        log_msg(f"📊 Export complete: {new_count} new, {updated_count} updated", "SUCCESS")
        return True
    except Exception as e:
        log_msg(f"❌ Export failed: {e}", "ERROR")
        return False

# === MAIN ===
def main():
    """Main execution"""
    log_msg("🚀 Starting Enhanced Scraper", "INFO")
    
    driver = setup_github_browser()
    if not driver:
        return
    
    try:
        if not login_to_damadam(driver):
            return
        
        client = get_google_sheets_client()
        if not client:
            return
        
        tags_mapping = get_tags_mapping(client, SHEET_URL)
        target_users = get_target_users(client, SHEET_URL)
        
        if not target_users:
            log_msg("❌ No target users found", "ERROR")
            return
        
        stats.total = len(target_users)
        scraped_profiles = []
        target_updates = []
        batch_size = GOOGLE_API_RATE_LIMIT['batch_size']
        
        log_msg(f"🎯 Processing {stats.total} users...", "INFO")
        
        for i, target_user in enumerate(target_users, 1):
            stats.current = i
            nickname = target_user['username']
            row_index = target_user['row_index']
            
            log_msg(f"🔍 Scraping: {nickname} ({i}/{stats.total})", "INFO")
            
            try:
                profile = scrape_profile(driver, nickname)
                
                if profile:
                    scraped_profiles.append(profile)
                    stats.success += 1
                    target_updates.append({
                        'row_index': row_index,
                        'status': 'Completed',
                        'notes': 'Successfully scraped'
                    })
                else:
                    stats.errors += 1
                    target_updates.append({
                        'row_index': row_index,
                        'status': 'Pending',
                        'notes': 'Failed - will retry'
                    })
                
                if len(scraped_profiles) >= batch_size or len(target_updates) >= batch_size:
                    log_msg(f"📤 Exporting batch of {len(scraped_profiles)} profiles...", "INFO")
                    if export_to_google_sheets_with_rate_limiting(scraped_profiles, tags_mapping, target_updates):
                        scraped_profiles = []
                        target_updates = []
                        time.sleep(10)
                    else:
                        log_msg("⚠️ Export failed, keeping data for retry", "WARNING")
            except Exception as e:
                stats.errors += 1
                log_msg(f"❌ Error: {e}", "ERROR")
                target_updates.append({
                    'row_index': row_index,
                    'status': 'Pending',
                    'notes': f'Error: {str(e)[:100]}'
                })
            
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        if scraped_profiles or target_updates:
            export_to_google_sheets_with_rate_limiting(scraped_profiles, tags_mapping, target_updates)
        
        stats.show_summary()
        log_msg(f"🎯 Completed: {stats.success}/{stats.total}", "INFO")
        log_msg(f"📝 Posts Scraped: {stats.posts_scraped}", "INFO")
    except Exception as e:
        log_msg(f"❌ Error: {e}", "ERROR")
    finally:
        try:
            driver.quit()
        except:
            pass
        log_msg("🏁 Done", "INFO")

if __name__ == "__main__":
    main()
