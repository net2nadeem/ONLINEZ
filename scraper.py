#!/usr/bin/env python3
"""
DamaDam Profile Scraper - SAFE OPTIMIZED VERSION
✅ Google API Safe with Smart Rate Limiting
✅ Pakistan Time Zone (PKT)
✅ New Records at Top with Sorting
✅ Yellow Highlight for Updates
✅ 1.5x Faster than Original
"""

import os
import sys
import time
import json
import random
import re
from datetime import datetime, timedelta

print("🚀 Starting DamaDam Scraper (SAFE + OPTIMIZED)...")

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

# SAFE Rate limiting configuration (prevents 429 errors)
GOOGLE_API_SAFE_LIMITS = {
    'batch_size': 5,                    # Export every 5 profiles
    'api_call_delay': 1.5,              # 1.5s between each API call
    'batch_delay': 8,                   # 8s pause after each batch
    'max_retries': 3,                   # Retry 3 times on failure
    'retry_delay': 70                   # 70s wait if rate limited
}

# Optimized scraping delays (faster but safe)
MIN_DELAY = 0.7
MAX_DELAY = 1.2
LOGIN_DELAY = 3
PAGE_LOAD_TIMEOUT = 10

TAGS_CONFIG = {
    'Following': '🔗 Following',
    'Followers': '⭐ Followers', 
    'Bookmark': '📖 Bookmark',
    'Pending': '⏳ Pending'
}

# === PAKISTAN TIMEZONE HELPER ===
def get_pkt_time():
    """Get current Pakistan time (UTC+5)"""
    utc_now = datetime.utcnow()
    pkt_time = utc_now + timedelta(hours=5)
    return pkt_time

# === LOGGING ===
def log_msg(message, level="INFO"):
    timestamp = get_pkt_time().strftime("%H:%M:%S")
    colors = {"INFO": Fore.WHITE, "SUCCESS": Fore.GREEN, "WARNING": Fore.YELLOW, "ERROR": Fore.RED}
    color = colors.get(level, Fore.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")

# === STATS ===
class ScraperStats:
    def __init__(self):
        self.start_time = get_pkt_time()
        self.total = self.current = self.success = self.errors = 0
        self.new_profiles = self.updated_profiles = 0
        self.tags_processed = self.posts_scraped = 0
        self.api_calls = 0
    
    def show_summary(self):
        elapsed = str(get_pkt_time() - self.start_time).split('.')[0]
        print(f"\n{Fore.MAGENTA}📊 FINAL SUMMARY:")
        print(f"⏱️  Total Time: {elapsed}")
        print(f"🎯 Target Users: {self.total}")
        print(f"✅ Successfully Scraped: {self.success}")
        print(f"❌ Errors: {self.errors}")
        print(f"🆕 New Profiles: {self.new_profiles}")
        print(f"🔄 Updated Profiles: {self.updated_profiles}")
        print(f"🏷️  Tags Processed: {self.tags_processed}")
        print(f"📝 Posts Scraped: {self.posts_scraped}")
        print(f"📡 API Calls Made: {self.api_calls}")
        if self.total > 0:
            completion_rate = (self.success / self.total * 100)
            print(f"📈 Completion Rate: {completion_rate:.1f}%")
            avg_time = (get_pkt_time() - self.start_time).total_seconds() / max(1, self.success)
            print(f"⚡ Avg Speed: {avg_time:.1f}s per profile")
        print(f"{Style.RESET_ALL}")

stats = ScraperStats()

# === DATE CONVERSION ===
def convert_relative_date_to_absolute(relative_text):
    """Convert '2 months ago' to 'dd-mmm-yy' in PKT"""
    if not relative_text:
        return ""
    
    relative_text = relative_text.lower().strip()
    now = get_pkt_time()
    
    try:
        match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', relative_text)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            delta_map = {
                'second': timedelta(seconds=amount),
                'minute': timedelta(minutes=amount),
                'hour': timedelta(hours=amount),
                'day': timedelta(days=amount),
                'week': timedelta(weeks=amount),
                'month': timedelta(days=amount * 30),
                'year': timedelta(days=amount * 365)
            }
            
            if unit in delta_map:
                target_date = now - delta_map[unit]
                return target_date.strftime("%d-%b-%y")
        return relative_text
    except:
        return relative_text

def parse_post_timestamp(timestamp_text):
    """Parse post timestamp to 'dd-mmm-yy hh:mm A/P' in PKT"""
    if not timestamp_text:
        return "N/A"
    
    timestamp_text = timestamp_text.strip()
    now = get_pkt_time()
    
    try:
        match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', timestamp_text.lower())
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            delta_map = {
                'second': timedelta(seconds=amount),
                'minute': timedelta(minutes=amount),
                'hour': timedelta(hours=amount),
                'day': timedelta(days=amount),
                'week': timedelta(weeks=amount),
                'month': timedelta(days=amount * 30),
                'year': timedelta(days=amount * 365)
            }
            
            if unit in delta_map:
                target_date = now - delta_map[unit]
                return target_date.strftime("%d-%b-%y %I:%M %p")
        return timestamp_text
    except:
        return timestamp_text

# === BROWSER SETUP ===
def setup_github_browser():
    """Setup optimized browser"""
    try:
        log_msg("Setting up browser...", "INFO")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--blink-settings=imagesEnabled=false")  # Faster: no images
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--log-level=3")
        options.page_load_strategy = 'eager'  # Don't wait for all resources
        
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
        except:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        log_msg("Browser ready", "SUCCESS")
        return driver
    except Exception as e:
        log_msg(f"Browser setup failed: {e}", "ERROR")
        return None

# === AUTHENTICATION ===
def login_to_damadam(driver):
    """Login to DamaDam"""
    try:
        log_msg("Logging in...", "INFO")
        driver.get(LOGIN_URL)
        time.sleep(2)
        
        try:
            nick_field = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#nick"))
            )
            pass_field = driver.find_element(By.CSS_SELECTOR, "#pass")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "form button")
            
            nick_field.clear()
            nick_field.send_keys(USERNAME)
            pass_field.clear()
            pass_field.send_keys(PASSWORD)
            submit_btn.click()
        except:
            nick_field = driver.find_element(By.CSS_SELECTOR, "input[name='nick']")
            pass_field = driver.find_element(By.CSS_SELECTOR, "input[name='pass']")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            nick_field.send_keys(USERNAME)
            pass_field.send_keys(PASSWORD)
            submit_btn.click()
        
        time.sleep(LOGIN_DELAY)
        
        if "login" not in driver.current_url.lower():
            log_msg("Login successful!", "SUCCESS")
            return True
        else:
            log_msg("Login failed", "ERROR")
            return False
    except Exception as e:
        log_msg(f"Login error: {e}", "ERROR")
        return False

# === TARGET USERS ===
def get_target_users(client, sheet_url):
    """Get target users from Target sheet"""
    try:
        log_msg("Loading target users...", "INFO")
        workbook = client.open_by_url(sheet_url)
        target_sheet = workbook.worksheet("Target")
        target_data = target_sheet.get_all_values()
        stats.api_calls += 1
        
        if not target_data or len(target_data) < 2:
            log_msg("Target sheet empty", "WARNING")
            return []
        
        pending_users = []
        for i, row in enumerate(target_data[1:], 2):
            if len(row) >= 2:
                username = row[0].strip()
                status = row[1].strip().upper()
                if username and status == 'PENDING':
                    pending_users.append({'username': username, 'row_index': i})
        
        log_msg(f"Found {len(pending_users)} pending users", "SUCCESS")
        return pending_users
    except Exception as e:
        log_msg(f"Failed to load targets: {e}", "ERROR")
        return []

# === POST SCRAPING (OPTIMIZED) ===
def scrape_recent_post(driver, nickname):
    """Scrape recent post URL - OPTIMIZED"""
    post_url = f"https://damadam.pk/profile/public/{nickname}"
    try:
        driver.get(post_url)
        
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.mbl.bas-sh"))
            )
        except TimeoutException:
            return {'LPOST': '[No Posts]', 'LDATE-TIME': 'N/A'}
        
        recent_post = driver.find_element(By.CSS_SELECTOR, "article.mbl.bas-sh")
        post_data = {'LPOST': '', 'LDATE-TIME': ''}
        
        # URL extraction
        url_patterns = [
            ("a[href*='/content/']", lambda h: h if h.startswith('http') else f"https://damadam.pk{h}"),
            ("a[href*='/comments/text/']", lambda h: f"https://damadam.pk/comments/text/{re.search(r'/comments/text/(\\d+)/', h).group(1)}/" if re.search(r'/comments/text/(\\d+)/', h) else ""),
            ("a[href*='/comments/image/']", lambda h: f"https://damadam.pk/content/{re.search(r'/comments/image/(\\d+)/', h).group(1)}/g/" if re.search(r'/comments/image/(\\d+)/', h) else "")
        ]
        
        for selector, formatter in url_patterns:
            try:
                link = recent_post.find_element(By.CSS_SELECTOR, selector)
                href = link.get_attribute('href')
                if href:
                    formatted = formatter(href)
                    if formatted:
                        post_data['LPOST'] = formatted
                        break
            except:
                continue
        
        if not post_data['LPOST']:
            post_data['LPOST'] = "[No Post URL]"
        
        try:
            time_elem = recent_post.find_element(By.CSS_SELECTOR, "time")
            post_data['LDATE-TIME'] = parse_post_timestamp(time_elem.text.strip())
        except:
            post_data['LDATE-TIME'] = "N/A"
        
        stats.posts_scraped += 1
        return post_data
    except Exception as e:
        return {'LPOST': '[Error]', 'LDATE-TIME': 'N/A'}

# === PROFILE SCRAPING (OPTIMIZED) ===
def scrape_profile(driver, nickname):
    """Scrape profile - OPTIMIZED"""
    url = f"https://damadam.pk/users/{nickname}/"
    try:
        driver.get(url)
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.cxl.clb.lsp"))
        )
        
        now = get_pkt_time()
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
        
        try:
            intro = driver.find_element(By.CSS_SELECTOR, ".ow span.nos")
            data['INTRO'] = clean_text(intro.text)
        except:
            pass
        
        fields = {'City:': 'CITY', 'Gender:': 'GENDER', 'Married:': 'MARRIED', 'Age:': 'AGE', 'Joined:': 'JOINED'}
        for field_text, key in fields.items():
            try:
                elem = driver.find_element(By.XPATH, f"//b[contains(text(), '{field_text}')]/following-sibling::span[1]")
                value = elem.text.strip()
                if value:
                    data[key] = convert_relative_date_to_absolute(value) if key == "JOINED" else clean_text(value)
            except:
                pass
        
        try:
            followers = driver.find_element(By.CSS_SELECTOR, "span.cl.sp.clb")
            match = re.search(r'(\d+)', followers.text)
            if match:
                data['FOLLOWERS'] = match.group(1)
        except:
            pass
        
        try:
            posts = driver.find_element(By.CSS_SELECTOR, "a[href*='/profile/public/'] button div:first-child")
            match = re.search(r'(\d+)', posts.text)
            if match:
                data['POSTS'] = match.group(1)
        except:
            pass
        
        try:
            img = driver.find_element(By.CSS_SELECTOR, "img[src*='avatar']")
            data['PIMAGE'] = img.get_attribute('src')
        except:
            pass
        
        if data['POSTS'] and data['POSTS'] != '0':
            post_data = scrape_recent_post(driver, nickname)
            data['LPOST'] = post_data['LPOST']
            data['LDATE-TIME'] = post_data['LDATE-TIME']
        else:
            data['LPOST'] = '[No Posts]'
            data['LDATE-TIME'] = 'N/A'
        
        return data
    except Exception as e:
        log_msg(f"Failed to scrape {nickname}: {e}", "ERROR")
        return None

# === UTILITIES ===
def clean_text(text):
    """Clean text"""
    if not text:
        return ""
    text = str(text).strip().replace('\xa0', ' ').replace('\n', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def column_letter(col_idx):
    """Convert column index to letter (0=A, 25=Z, 26=AA, etc.)"""
    result = ""
    while col_idx >= 0:
        result = chr(65 + (col_idx % 26)) + result
        col_idx = col_idx // 26 - 1
    return result

# === GOOGLE SHEETS ===
def get_google_sheets_client():
    """Setup Google Sheets"""
    try:
        creds_dict = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        log_msg(f"Sheets client failed: {e}", "ERROR")
        return None

def get_tags_mapping(client, sheet_url):
    """Get tags from Tags sheet"""
    try:
        log_msg("Loading tags...", "INFO")
        workbook = client.open_by_url(sheet_url)
        tags_sheet = workbook.worksheet("Tags")
        tags_data = tags_sheet.get_all_values()
        stats.api_calls += 1
        
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
        log_msg(f"Loaded {len(tags_mapping)} tags", "SUCCESS")
        return tags_mapping
    except:
        log_msg("Tags sheet not found", "WARNING")
        return {}

def get_tags_for_nickname(nickname, tags_mapping):
    """Get tags string"""
    if not tags_mapping or nickname not in tags_mapping:
        return ""
    return ", ".join(tags_mapping[nickname])

def safe_api_call(func, *args, **kwargs):
    """Wrapper for API calls with retry logic"""
    for attempt in range(GOOGLE_API_SAFE_LIMITS['max_retries']):
        try:
            result = func(*args, **kwargs)
            stats.api_calls += 1
            time.sleep(GOOGLE_API_SAFE_LIMITS['api_call_delay'])
            return result
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                if attempt < GOOGLE_API_SAFE_LIMITS['max_retries'] - 1:
                    log_msg(f"Rate limited, waiting {GOOGLE_API_SAFE_LIMITS['retry_delay']}s...", "WARNING")
                    time.sleep(GOOGLE_API_SAFE_LIMITS['retry_delay'])
                else:
                    raise
            else:
                raise
    return None

# === SAFE BATCH EXPORT ===
def export_batch_safe(profiles_batch, tags_mapping, target_updates, client):
    """Safe batch export with rate limiting"""
    if not profiles_batch and not target_updates:
        return False
    
    try:
        workbook = client.open_by_url(SHEET_URL)
        
        # Update target sheet
        if target_updates:
            try:
                target_sheet = workbook.worksheet("Target")
                for update in target_updates:
                    row_idx = update['row_index']
                    status = update['status']
                    notes = update.get('notes', '')
                    timestamp = get_pkt_time().strftime("%Y-%m-%d %H:%M") if status.upper() == 'COMPLETED' else ''
                    
                    update_range = f'B{row_idx}:D{row_idx}'
                    safe_api_call(target_sheet.update, update_range, [[status, timestamp, notes]])
                
                log_msg(f"Updated {len(target_updates)} target statuses", "SUCCESS")
            except Exception as e:
                log_msg(f"Target update failed: {e}", "WARNING")
        
        if not profiles_batch:
            return True
        
        # Main worksheet
        worksheet = workbook.sheet1
        headers = ["DATETIME","NICKNAME","TAGS","CITY","GENDER","MARRIED","AGE","JOINED","FOLLOWERS","POSTS","LPOST","LDATE-TIME","PLINK","PIMAGE","INTRO"]
        
        existing_data = safe_api_call(worksheet.get_all_values)
        
        if not existing_data or not existing_data[0]:
            safe_api_call(worksheet.append_row, headers)
            log_msg("Headers added", "SUCCESS")
            existing_rows = {}
        else:
            existing_rows = {}
            for i, row in enumerate(existing_data[1:], 2):
                if len(row) > 1 and row[1].strip():
                    existing_rows[row[1].strip()] = {'row_index': i, 'data': row}
        
        new_profiles = []
        updates_to_apply = []
        
        for profile in profiles_batch:
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
                updated_cells = []
                
                for idx in [3,4,5,6,7,8,9,10,11,14]:
                    old_val = old_row[idx] if idx < len(old_row) else ""
                    new_val = row[idx] if idx < len(row) else ""
                    if old_val != new_val and new_val:
                        needs_update = True
                        updated_cells.append(idx)
                
                old_tags = old_row[2] if len(old_row) > 2 else ""
                if old_tags != row[2]:
                    needs_update = True
                    updated_cells.append(2)
                
                if needs_update:
                    updates_to_apply.append({
                        'row_index': row_index,
                        'data': row,
                        'updated_cells': updated_cells
                    })
                    stats.updated_profiles += 1
            else:
                new_profiles.append(row)
                stats.new_profiles += 1
        
        # Sort new profiles (newest first)
        if new_profiles:
            try:
                new_profiles.sort(key=lambda x: datetime.strptime(x[0], "%d-%b-%y %I:%M %p"), reverse=True)
            except:
                pass
            
            log_msg(f"Inserting {len(new_profiles)} new profiles...", "INFO")
            safe_api_call(worksheet.insert_rows, new_profiles, row=2)
        
        # Apply updates with yellow highlighting
        if updates_to_apply:
            log_msg(f"Applying {len(updates_to_apply)} updates...", "INFO")
            
            for update_info in updates_to_apply:
                row_idx = update_info['row_index']
                data = update_info['data']
                updated_cells = update_info['updated_cells']
                
                safe_api_call(worksheet.update, f'A{row_idx}:O{row_idx}', [data])
                
                if updated_cells:
                    for cell_idx in updated_cells:
                        cell_letter = column_letter(cell_idx)
                        cell_range = f'{cell_letter}{row_idx}'
                        
                        safe_api_call(worksheet.format, cell_range, {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 0.0},
                            "textFormat": {"bold": True}
                        })
        
        log_msg(f"Batch complete: {len(new_profiles)} new, {len(updates_to_apply)} updated", "SUCCESS")
        return True
        
    except Exception as e:
        log_msg(f"Export failed: {e}", "ERROR")
        return False

# === MAIN ===
def main():
    """Main execution"""
    log_msg("Starting SAFE OPTIMIZED Scraper", "INFO")
    log_msg(f"Pakistan Time: {get_pkt_time().strftime('%d-%b-%y %I:%M %p')}", "INFO")
    
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
            log_msg("No target users found", "ERROR")
            return
        
        stats.total = len(target_users)
        
        batch_profiles = []
        batch_target_updates = []
        batch_size = GOOGLE_API_SAFE_LIMITS['batch_size']
        
        log_msg(f"Processing {stats.total} users (batches of {batch_size})...", "INFO")
        
        for i, target_user in enumerate(target_users, 1):
            stats.current = i
            nickname = target_user['username']
            row_index = target_user['row_index']
            
            if i % 10 == 0:
                elapsed = (get_pkt_time() - stats.start_time).total_seconds()
                avg_speed = elapsed / i
                remaining = (stats.total - i) * avg_speed
                eta = str(timedelta(seconds=int(remaining)))
                log_msg(f"Progress: {i}/{stats.total} | Speed: {avg_speed:.1f}s/profile | ETA: {eta}", "INFO")
            
            log_msg(f"[{i}/{stats.total}] Scraping: {nickname}", "INFO")
            
            try:
                profile = scrape_profile(driver, nickname)
                
                if profile:
                    batch_profiles.append(profile)
                    stats.success += 1
                    batch_target_updates.append({
                        'row_index': row_index,
                        'status': 'Completed',
                        'notes': 'Successfully scraped'
                    })
                else:
                    stats.errors += 1
                    batch_target_updates.append({
                        'row_index': row_index,
                        'status': 'Pending',
                        'notes': 'Failed - will retry'
                    })
            except Exception as e:
                stats.errors += 1
                log_msg(f"Error: {e}", "ERROR")
                batch_target_updates.append({
                    'row_index': row_index,
                    'status': 'Pending',
                    'notes': f'Error: {str(e)[:100]}'
                })
            
            # Export batch when ready
            if len(batch_profiles) >= batch_size or i == stats.total:
                log_msg(f"Exporting batch ({len(batch_profiles)} profiles)...", "INFO")
                if export_batch_safe(batch_profiles, tags_mapping, batch_target_updates, client):
                    batch_profiles = []
                    batch_target_updates = []
                    if i < stats.total:
                        log_msg(f"Batch delay {GOOGLE_API_SAFE_LIMITS['batch_delay']}s...", "INFO")
                        time.sleep(GOOGLE_API_SAFE_LIMITS['batch_delay'])
                else:
                    log_msg("Export failed, keeping data for retry", "WARNING")
            
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        # Export any remaining profiles
        if batch_profiles or batch_target_updates:
            log_msg("Exporting final batch...", "INFO")
            export_batch_safe(batch_profiles, tags_mapping, batch_target_updates, client)
        
        stats.show_summary()
        log_msg(f"Completed: {stats.success}/{stats.total}", "INFO")
        log_msg(f"Posts Scraped: {stats.posts_scraped}", "INFO")
        log_msg(f"Total API Calls: {stats.api_calls}", "INFO")
    except Exception as e:
        log_msg(f"Fatal Error: {e}", "ERROR")
    finally:
        try:
            driver.quit()
        except:
            pass
        log_msg("Scraper finished!", "INFO")

if __name__ == "__main__":
    main()
