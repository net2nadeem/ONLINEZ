import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from colorama import Fore, Style, init
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Initialize colorama
init(autoreset=True)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("online.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1XQxDCZYy47oqA5-4PdZ1X_WO4Jhy1BIWWNmXBqJX-FE").sheet1

# Login credentials
USERNAME = "0utLawZ"
PASSWORD = "@Brandex1999"

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Run headless for GitHub Actions
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)

# Login function
def login():
    driver.get("https://damadam.pk/")
    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//button[contains(text(),"Login")]').click()
    print(Fore.GREEN + "✅ Login successful")

# Scrape followers
def scrape_followers():
    driver.get("https://damadam.pk/outlawz/followers")
    time.sleep(3)
    followers = driver.find_elements(By.CLASS_NAME, "user-list-item")
    scraped = []

    for idx, f in enumerate(followers, start=1):
        try:
            name = f.find_element(By.CLASS_NAME, "username").text
            profile_url = f.find_element(By.TAG_NAME, "a").get_attribute("href")
            scraped.append([name, profile_url])
            print(Fore.CYAN + f"[{idx}] {name} - {profile_url}")

            # Batch Google Sheets export (every 10 profiles)
            if len(scraped) % 10 == 0:
                export_to_google_sheets(scraped[-10:])

        except Exception as e:
            print(Fore.RED + f"⚠ Error scraping follower {idx}: {e}")

    # Export remaining profiles (if less than 10 left at the end)
    remaining = len(scraped) % 10
    if remaining > 0:
        export_to_google_sheets(scraped[-remaining:])

    return scraped

# Export to Google Sheets
def export_to_google_sheets(data):
    sheet.append_rows(data)
    print(Fore.YELLOW + f"📤 Exported {len(data)} profiles to Google Sheets")

# Main
if __name__ == "__main__":
    login()
    followers_data = scrape_followers()
    print(Fore.MAGENTA + f"🎉 Scraping complete. Total: {len(followers_data)} followers")
    driver.quit()
