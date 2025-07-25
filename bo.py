import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
import logging

# Set up logging to print to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Google Sheets API setup ---
try:
    # Get the JSON key from the environment variable
    gcp_json_credentials_str = os.environ.get('GCP_SA_KEY')
    if not gcp_json_credentials_str:
        raise ValueError("GCP_SA_KEY environment variable not set.")

    # Convert the JSON string to a dictionary
    gcp_json_credentials = json.loads(gcp_json_credentials_str)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_json_credentials, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1Hd2TbGozRvRqJKpnpKa3CDF_X_V9wXNYt5aXivHbats/edit?gid=1293804849#gid=1293804849"
    ).worksheet("TEST3")
    logging.info("Connected to Google Sheet successfully")
except Exception as e:
    logging.error(f"Failed to connect to Google Sheet: {e}")
    exit(1)

# List of websites and credentials
websites = [
    {"user": "cxbert", "password": "Welcome1", "url": "https://www.jeetfun.com/page/manager/login.jsp"},
    {"user": "vprmon01", "password": "Welcome1", "url": "https://marvelback.com/page/manager/dashboard.jsp"},
    {"user": "mpbert", "password": "Welcome1", "url": "https://mpback1.com/page/manager/login.jsp"},
    {"user": "dpbert", "password": "Welcome1", "url": "https://dpoffice1.com/page/manager/dashboard.jsp"},
    {"user": "kvbert", "password": "Welcome1", "url": "https://kvoffice1.com/page/manager/dashboard.jsp"},
    {"user": "hbmon04", "password": "Welcome1", "url": "https://hboffice1.com/page/manager/dashboard.jsp"},
    {"user": "jbbert", "password": "Welcome1", "url": "https://jboffice1.com/page/manager/dashboard.jsp"},
    {"user": "jwbert", "password": "Welcome3333", "url": "https://jwoffice1.com/page/manager/dashboard.jsp"},
    {"user": "sbmon03", "password": "welcome2", "url": "https://sboffice1.com/page/manager/dashboard.jsp"},
    {"user": "slbmon02", "password": "welcome888", "url": "https://sbajioffice1.com/page/manager/dashboard.jsp"},
    {"user": "bjdmon02", "password": "Welcome23", "url": "https://bjdoffice1.com/page/manager/dashboard.jsp"}
]

# Function to process a single website
def process_website(site):
    driver = None
    try:
        options = Options()
        # --- KEY CHANGES FOR RENDER ---
        options.add_argument("--headless")  # Must be enabled for cloud environments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # -----------------------------
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info(f"Thread for {site['url']}: Chrome browser initialized")
    except Exception as e:
        logging.error(f"Thread for {site['url']}: Failed to initialize Chrome: {e}")
        return [site["url"], "Browser Error", "Browser Error"]

    try:
        logging.info(f"Thread for {site['url']}: Processing")
        driver.get(site["url"])
        
        # Step 1: Input username
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/form/div[2]/div/input"))
            )
            username_field.send_keys(site["user"])
        except Exception:
            logging.error(f"Thread for {site['url']}: Username input failed")
            return [site["url"], "Username Error", "Username Error"]

        # Step 2: Input password
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/form/div[3]/div/input"))
            )
            password_field.send_keys(site["password"])
        except Exception:
            logging.error(f"Thread for {site['url']}: Password input failed")
            return [site["url"], "Password Error", "Password Error"]

        # Step 3: Click login button
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/form/div[6]/a"))
            )
            login_button.click()
            time.sleep(2) # Wait for page to load after login
        except Exception:
            logging.error(f"Thread for {site['url']}: Login button failed")
            return [site["url"], "Login Error", "Login Error"]

        # Step 4: Handle currency selection
        currency_sites = [
            "https://www.jeetfun.com/page/manager/login.jsp",
            "https://marvelback.com/page/manager/dashboard.jsp",
            "https://mpback1.com/page/manager/login.jsp",
            "https://jwoffice1.com/page/manager/dashboard.jsp"
        ]
        if site["url"] in currency_sites:
            try:
                option_index = 3 if site["url"] == "https://marvelback.com/page/manager/dashboard.jsp" else 2
                currency_xpath = f"/html/body/div[5]/div[2]/div/div[1]/ul[2]/li/a/span[2]/select/option[{option_index}]"
                currency_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, currency_xpath))
                )
                currency_option.click()
                logging.info(f"Thread for {site['url']}: Selected currency: {currency_option.text.strip()}")
                time.sleep(5) # Wait for data to refresh after currency change
            except Exception as e:
                logging.error(f"Thread for {site['url']}: Currency selection error: {e}")
                return [site["url"], "Currency Error", "Currency Error"]

        # Step 5: Extract data
        try:
            data_b_xpath = "/html/body/div[5]/div[2]/div/div[4]/div[1]/div/div[2]/ul/li[2]/strong"
            data_c_xpath = "/html/body/div[5]/div[2]/div/div[4]/div[2]/div/div[2]/ul/li[2]/strong"

            data_b = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, data_b_xpath))).text.strip()
            data_c = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, data_c_xpath))).text.strip()
            logging.info(f"Extracted data for {site['url']}: B={data_b}, C={data_c}")
            return [site["url"], data_b, data_c]
        except Exception as e:
            logging.error(f"Thread for {site['url']}: Data extraction error: {e}")
            return [site["url"], "Data Error", "Data Error"]
    except Exception as e:
        logging.error(f"Thread for {site['url']}: General processing error: {e}")
        return [site["url"], "General Error", "General Error"]
    finally:
        if driver:
            driver.quit()

# Main function
def scrape_and_update():
    start_time = time.time()
    logging.info("Starting new scrape cycle...")

    data_map = {site["url"]: ["", ""] for site in websites}
    with ThreadPoolExecutor(max_workers=4) as executor: # Increased workers for faster execution
        future_to_site = {executor.submit(process_website, site): site for site in websites}
        for future in as_completed(future_to_site):
            site = future_to_site[future]
            try:
                result = future.result()
                if result:
                    data_map[site["url"]] = [result[1], result[2]]
            except Exception as exc:
                logging.error(f"{site['url']} generated an exception: {exc}")
                data_map[site['url']] = ["Exception", "Exception"]


    data_to_write = [data_map[site["url"]] for site in websites]

    try:
        sheet.update(range_name="B2", values=data_to_write)
        logging.info(f"Data written to Google Sheet: {data_to_write}")
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.update(range_name='D1', values=[[current_time_str]])
        logging.info(f"Timestamp written to D1: {current_time_str}")
    except Exception as e:
        logging.error(f"Error updating Google Sheet: {e}")

    logging.info(f"Scrape cycle completed in {time.time() - start_time:.2f} seconds")

# --- Main execution loop ---
if __name__ == "__main__":
    scrape_and_update() # Run once immediately on start
    schedule.every(1).minutes.do(scrape_and_update)
    logging.info("Scheduler started. Will run every 1 minute.")
    while True:
        schedule.run_pending()
        time.sleep(1)