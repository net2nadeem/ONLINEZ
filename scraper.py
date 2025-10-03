#!/usr/bin/env python3
"""
DamaDam Profile Scraper – Optimized for speed, Pakistan time, and a tidy Google Sheet
"""

import os
import sys
import time
import json
import re
import random
from datetime import datetime, timedelta, timezone

# -------------------------- Logging ---------------------------------
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    LOG_COLORS = {
        "INFO": Fore.WHITE,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
    }
except Exception:
    LOG_COLORS = {"INFO": "", "SUCCESS": "", "WARNING": "", "ERROR": ""}
    class Style:
        RESET_ALL = ""


def log_msg(message, level="INFO"):
    ts = datetime.now(timezone(timedelta(hours=5))).strftime("%H:%M:%S")
    print(f"{LOG_COLORS.get(level, '')}[{ts}] {level}: {message}{Style.RESET_ALL}")


# -------------------------- Config ----------------------------------
LOGIN_URL = "https://damadam.pk/login/"
MIN_DELAY = 0.8
MAX_DELAY = 1.2
LOGIN_DELAY = 2.0

# Tag icons
TAGS_CONFIG = {
    "Following": "🔗 Following",
    "Followers": "⭐ Followers",
    "Bookmark": "📖 Bookmark",
    "Pending": "⏳ Pending",
}

# Rate‑limit (Google‑Sheets API)
GOOGLE_API_RATE_LIMIT = {
    "max_requests_per_minute": 50,
    "batch_size": 3,
    "retry_delay": 65,  # seconds
    "request_delay": 1.2,
}
api_request_times = []


def track_api_request():
    """Enforce Google‑Sheets API rate‑limit."""
    now = datetime.now(timezone(timedelta(hours=5)))
    global api_request_times
    api_request_times = [t for t in api_request_times if (now - t).total_seconds() < 60]
    api_request_times.append(now)
    if len(api_request_times) >= GOOGLE_API_RATE_LIMIT["max_requests_per_minute"]:
        log_msg("⚠️  Google‑Sheets API rate‑limit reached – sleeping …", "WARNING")
        time.sleep(GOOGLE_API_RATE_LIMIT["retry_delay"])
        api_request_times = []


# -------------------------- Packages --------------------------------
# Selenium + webdriver‑manager
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    log_msg("✅ Selenium ready", "SUCCESS")
except ImportError:
    log_msg("❌ Selenium or webdriver‑manager missing", "ERROR")
    sys.exit(1)

# gspread + oauth2client
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    log_msg("✅ Google Sheets ready", "SUCCESS")
except ImportError:
    log_msg("❌ gspread or oauth2client missing", "ERROR")
    sys.exit(1)


# -------------------------- Environment --------------------------------
USERNAME = os.getenv("DAMADAM_USERNAME")
PASSWORD = os.getenv("DAMADAM_PASSWORD")
SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

if not all([USERNAME, PASSWORD, SHEET_URL, GOOGLE_SERVICE_ACCOUNT_JSON]):
    log_msg(
        "❌ Missing one or more required environment variables:\n"
        "    DAMADAM_USERNAME, DAMADAM_PASSWORD, GOOGLE_SHEET_URL, GOOGLE_SERVICE_ACCOUNT_JSON",
        "ERROR",
    )
    sys.exit(1)


# -------------------------- Time helpers --------------------------------
PKT = timezone(timedelta(hours=5))  # Pakistan Standard Time


def now_pkt():
    return datetime.now(PKT)


def format_pkt(dt: datetime | None = None, fmt="%d-%b-%y %I:%M %p"):
    if dt is None:
        dt = now_pkt()
    return dt.strftime(fmt)


# -------------------------- Utilities ------------------------------------
def rand_sleep():
    """Short random delay to make Selenium look a little natural."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def clean_text(txt: str) -> str:
    if not txt:
        return ""
    txt = str(txt).replace("\xa0", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", txt).strip()


def convert_relative_date_to_absolute(relative_text: str) -> str:
    """Turn '2 months ago' → 'dd‑mmm‑yy' (Pakistan time)."""
    if not relative_text:
        return ""

    relative_text = relative_text.lower().strip()
    now = now_pkt()

    m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago", relative_text)
    if not m:
        return relative_text

    amount, unit = int(m.group(1)), m.group(2)
    if unit == "second":
        delta = timedelta(seconds=amount)
    elif unit == "minute":
        delta = timedelta(minutes=amount)
    elif unit == "hour":
        delta = timedelta(hours=amount)
    elif unit == "day":
        delta = timedelta(days=amount)
    elif unit == "week":
        delta = timedelta(weeks=amount)
    elif unit == "month":
        delta = timedelta(days=30 * amount)
    elif unit == "year":
        delta = timedelta(days=365 * amount)
    else:
        return relative_text

    target = now - delta
    return target.strftime("%d-%b-%y")


def parse_post_timestamp(ts_text: str) -> str:
    """Turn relative post time → 'dd‑mmm‑yy hh:mm AM/PM'."""
    if not ts_text:
        return "N/A"

    ts_text = ts_text.strip()
    now = now_pkt()

    m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago", ts_text.lower())
    if not m:
        return ts_text

    amount, unit = int(m.group(1)), m.group(2)
    if unit == "second":
        delta = timedelta(seconds=amount)
    elif unit == "minute":
        delta = timedelta(minutes=amount)
    elif unit == "hour":
        delta = timedelta(hours=amount)
    elif unit == "day":
        delta = timedelta(days=amount)
    elif unit == "week":
        delta = timedelta(weeks=amount)
    elif unit == "month":
        delta = timedelta(days=30 * amount)
    elif unit == "year":
        delta = timedelta(days=365 * amount)
    else:
        return ts_text

    target = now - delta
    return target.strftime("%d-%b-%y %I:%M %p")


# -------------------------- Browser ------------------------------------
def init_browser():
    log_msg("🚀 Initializing Chrome …")
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
    except Exception:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(15)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    log_msg("✅ Browser ready", "SUCCESS")
    return driver


# -------------------------- Login ------------------------------------
def login_to_damadam(driver):
    log_msg("🔐 Logging in …")
    driver.get(LOGIN_URL)
    rand_sleep()

    # Two common selector sets; try them in order
    selector_sets = [
        {"nick": "#nick", "pw": "#pass", "btn": "form button"},
        {"nick": "input[name='nick']", "pw": "input[name='pass']", "btn": "button[type='submit']"},
    ]

    for s in selector_sets:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, s["nick"])))
            driver.find_element(By.CSS_SELECTOR, s["nick"]).clear()
            rand_sleep()
            driver.find_element(By.CSS_SELECTOR, s["nick"]).send_keys(USERNAME)
            driver.find_element(By.CSS_SELECTOR, s["pw"]).clear()
            rand_sleep()
            driver.find_element(By.CSS_SELECTOR, s["pw"]).send_keys(PASSWORD)
            driver.find_element(By.CSS_SELECTOR, s["btn"]).click()
            rand_sleep()
            if "login" not in driver.current_url.lower():
                log_msg("✅ Login successful", "SUCCESS")
                return True
        except Exception:
            continue

    log_msg("❌ Login failed", "ERROR")
    return False


# -------------------------- Target users --------------------------------
def get_target_users(client):
    """Return list of dicts: {'username': str, 'row_index': int} for PENDING rows."""
    log_msg("🎯 Loading target users …")
    wb = client.open_by_url(SHEET_URL)
    sht = wb.worksheet("Target")
    data = sht.get_all_values()
    if len(data) < 2:
        log_msg("⚠️ Target sheet empty", "WARNING")
        return []

    pending = []
    for idx, row in enumerate(data[1:], 2):
        if len(row) >= 2 and row[0].strip() and row[1].strip().upper() == "PENDING":
            pending.append({"username": row[0].strip(), "row_index": idx})
    log_msg(f"✅ Found {len(pending)} pending users", "SUCCESS")
    return pending


# -------------------------- Tags ------------------------------------
def load_tags_mapping(client):
    """Return dict {nickname: [icon1, icon2, …]}"""
    log_msg("🏷️ Loading tags …")
    wb = client.open_by_url(SHEET_URL)
    sht = wb.worksheet("Tags")
    data = sht.get_all_values()
    if not data:
        log_msg("⚠️ Tags sheet empty", "WARNING")
        return {}

    mapping = {}
    headers = data[0]
    for col_idx, header in enumerate(headers):
        if not header.strip():
            continue
        icon = TAGS_CONFIG.get(header.strip(), f"🔌 {header.strip()}")
        for row in data[1:]:
            if col_idx < len(row) and row[col_idx].strip():
                nick = row[col_idx].strip()
                mapping.setdefault(nick, []).append(icon)

    log_msg(f"✅ Loaded tags for {len(mapping)} nicknames", "SUCCESS")
    return mapping


def get_tags_for_nick(nick, mapping):
    return ", ".join(mapping.get(nick, []))


# -------------------------- Recent Post --------------------------------
def scrape_recent_post(driver, nick):
    url = f"https://damadam.pk/profile/public/{nick}"
    log_msg(f"📝 Scraping recent post for {nick} …", "INFO")
    driver.get(url)
    try:
        WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.mbl.bas-sh"))
        )
    except TimeoutException:
        log_msg(f"⏳ No recent post found for {nick}", "WARNING")
        return {"LPOST": "[No Post]", "LDATE-TIME": "N/A"}

    article = driver.find_element(By.CSS_SELECTOR, "article.mbl.bas-sh")
    post_data = {"LPOST": "[No Post]", "LDATE-TIME": "N/A"}

    # URL extraction
    url_selectors = [
        "a[href*='/content/']",
        "a[href*='/comments/text/']",
        "a[href*='/comments/image/']",
    ]
    for sel in url_selectors:
        try:
            el = article.find_element(By.CSS_SELECTOR, sel)
            href = el.get_attribute("href")
            if href:
                if "/content/" in href:
                    post_data["LPOST"] = href if href.startswith("http") else f"https://damadam.pk{href}"
                    break
                if "/comments/text/" in href:
                    m = re.search(r"/comments/text/(\d+)/", href)
                    if m:
                        post_data["LPOST"] = f"https://damadam.pk/comments/text/{m.group(1)}/"
                        break
                if "/comments/image/" in href:
                    m = re.search(r"/comments/image/(\d+)/", href)
                    if m:
                        post_data["LPOST"] = f"https://damadam.pk/content/{m.group(1)}/g/"
                        break
        except Exception:
            continue

    # Timestamp
    for sel in ["time[itemprop='datePublished']", "time"]:
        try:
            el = article.find_element(By.CSS_SELECTOR, sel)
            if el.text.strip():
                post_data["LDATE-TIME"] = parse_post_timestamp(el.text.strip())
                break
        except Exception:
            continue

    log_msg(f"✅ Post URL: {post_data['LPOST']}", "SUCCESS")
    return post_data


# -------------------------- Profile ------------------------------------
def scrape_profile(driver, nick):
    url = f"https://damadam.pk/users/{nick}/"
    log_msg(f"🔍 Scraping profile {nick} …", "INFO")
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.cxl.clb.lsp"))
        )
    except TimeoutException:
        log_msg(f"❌ Profile page not found: {nick}", "ERROR")
        return None

    now_str = format_pkt()
    data = {
        "DATETIME": now_str,
        "NICKNAME": nick,
        "TAGS": "",
        "CITY": "",
        "GENDER": "",
        "MARRIED": "",
        "AGE": "",
        "JOINED": "",
        "FOLLOWERS": "",
        "POSTS": "",
        "LPOST": "",
        "LDATE-TIME": "",
        "PLINK": url,
        "PIMAGE": "",
        "INTRO": "",
    }

    # Intro
    for sel in [".ow span.nos", ".ow .nos", "span.nos"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.text.strip():
                data["INTRO"] = clean_text(el.text)
                break
        except Exception:
            continue

    # Field extraction
    field_map = {
        "City:": "CITY",
        "Gender:": "GENDER",
        "Married:": "MARRIED",
        "Age:": "AGE",
        "Joined:": "JOINED",
    }
    for txt, key in field_map.items():
        try:
            el = driver.find_element(
                By.XPATH, f"//b[contains(text(), '{txt}')]/following-sibling::span[1]"
            )
            val = el.text.strip()
            if val:
                data[key] = (
                    convert_relative_date_to_absolute(val)
                    if key == "JOINED"
                    else clean_text(val)
                )
        except Exception:
            continue

    # Followers count
    for sel in ["span.cl.sp.clb", ".cl.sp.clb"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            m = re.search(r"(\d+)", el.text)
            if m:
                data["FOLLOWERS"] = m.group(1)
                break
        except Exception:
            continue

    # Posts count
    for sel in ["a[href*='/profile/public/'] button div:first-child", "a[href*='/profile/public/'] button div"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            m = re.search(r"(\d+)", el.text)
            if m:
                data["POSTS"] = m.group(1)
                break
        except Exception:
            continue

    # Profile image
    for sel in ["img[src*='avatar-imgs']", "img[src*='avatar']"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            data["PIMAGE"] = el.get_attribute("src")
            break
        except Exception:
            continue

    # Recent post
    rand_sleep()
    post_data = scrape_recent_post(driver, nick)
    data["LPOST"] = post_data["LPOST"]
    data["LDATE-TIME"] = post_data["LDATE-TIME"]

    return data


# -------------------------- Google Sheets Export -----------------------
def insert_row_at_top(sheet, row_data):
    """Insert a new row right below the header (row 2)."""
    # Insert empty row
    sheet.insert_row([], index=2)
    # Update the new row
    sheet.update("A2:Z2", [row_data])


def export_to_google_sheets(
    client,
    profiles,
    tags_mapping,
    target_updates,  # list of dicts: {'row_index': int, 'status': str, 'notes': str}
):
    """
    Batch‑write profile rows and target‑sheet status updates.
    """
    if not profiles and not target_updates:
        return True

    log_msg("📊 Exporting to Google Sheets …", "INFO")
    wb = client.open_by_url(SHEET_URL)
    profile_sht = wb.worksheet("Profile")

    # 1. Insert new rows at top (one for each profile) – this keeps the latest data visible.
    for profile in reversed(profiles):
        row_data = [
            profile["DATETIME"],
            profile["NICKNAME"],
            get_tags_for_nick(profile["NICKNAME"], tags_mapping),
            profile["CITY"],
            profile["GENDER"],
            profile["MARRIED"],
            profile["AGE"],
            profile["JOINED"],
            profile["FOLLOWERS"],
            profile["POSTS"],
            profile["LPOST"],
            profile["LDATE-TIME"],
            profile["PLINK"],
            profile["PIMAGE"],
            profile["INTRO"],
        ]
        insert_row_at_top(profile_sht, row_data)
        rand_sleep()  # slight delay to stay within rate‑limit

    # 2. Batch update target sheet
    if target_updates:
        target_sht = wb.worksheet("Target")
        for upd in target_updates:
            track_api_request()
            row = upd["row_index"]
            status = upd["status"]
            notes = upd.get("notes", "")
            # Columns: B – status, C – note, D – completed timestamp
            target_sht.update(f"B{row}:D{row}", [[status, notes, status.upper() == "COMPLETED" and now_pkt().strftime("%Y-%m-%d %H:%M") or ""]])
            rand_sleep()
    return True


# -------------------------- Main ------------------------------------
def main():
    driver = init_browser()
    if not login_to_damadam(driver):
        driver.quit()
        sys.exit(1)

    client = get_google_sheets_client()
    if not client:
        driver.quit()
        sys.exit(1)

    tags_mapping = load_tags_mapping(client)

    pending = get_target_users(client)
    if not pending:
        log_msg("✅ No pending users – finished", "SUCCESS")
        driver.quit()
        return

    profiles_batch = []
    updates_batch = []

    for idx, user in enumerate(pending, 1):
        log_msg(f"🔹 ({idx}/{len(pending)}) Processing {user['username']} …", "INFO")
        data = scrape_profile(driver, user["username"])
        if not data:
            updates_batch.append({"row_index": user["row_index"], "status": "FAILED", "notes": "Scrape error"})
            continue

        data["TAGS"] = get_tags_for_nick(user["username"], tags_mapping)
        profiles_batch.append(data)

        updates_batch.append(
            {"row_index": user["row_index"], "status": "COMPLETED", "notes": ""}
        )

        # Export every batch_size profiles to keep the script fast
        if len(profiles_batch) >= GOOGLE_API_RATE_LIMIT["batch_size"]:
            export_to_google_sheets(client, profiles_batch, tags_mapping, updates_batch)
            profiles_batch.clear()
            updates_batch.clear()

        # Short pause to stay well below the 50‑req/min limit
        time.sleep(GOOGLE_API_RATE_LIMIT["request_delay"])

    # Final export for any remaining data
    if profiles_batch or updates_batch:
        export_to_google_sheets(client, profiles_batch, tags_mapping, updates_batch)

    log_msg("✅ All done!", "SUCCESS")
    driver.quit()


if __name__ == "__main__":
    main()