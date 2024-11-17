from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import requests
import random
import openpyxl
import time
from itertools import cycle

def set_up_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    return driver

def rotate_proxies():
    proxies = [
        "http://username:password@proxy1:port",
        "http://username:password@proxy2:port",
        "http://username:password@proxy3:port",
    ]
    return cycle(proxies)

def scrape_dynamic_site(base_url, total_pages, use_selenium=True):
    data = []
    driver = None

    if use_selenium:
        driver = set_up_driver()

    try:
        for page in range(1, total_pages + 1):
            url = f"{base_url}?page={page}"

            if use_selenium:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(random.uniform(2, 5))
                soup = BeautifulSoup(driver.page_source, "html.parser")
            else:
                proxy_pool = rotate_proxies()
                proxies = {"http": next(proxy_pool), "https": next(proxy_pool)}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(url, headers=headers, proxies=proxies)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.text, "html.parser")

            companies = soup.find_all("div", class_="result")

            for company in companies:
                try:
                    name = company.find("h2", class_="name").text.strip() if company.find("h2", class_="name") else "N/A"
                    website = company.find("a", href=True)["href"] if company.find("a", href=True) else "N/A"
                    contact = company.find("span", class_="contact").text.strip() if company.find("span", class_="contact") else "N/A"
                    address = company.find("p", class_="address").text.strip() if company.find("p", class_="address") else "N/A"
                    description = company.find("p", class_="description").text.strip() if company.find("p", class_="description") else "N/A"
                    data.append([name, website, contact, address, description])
                except Exception:
                    pass
    finally:
        if driver:
            driver.quit()

    save_to_excel(data)

def save_to_excel(data):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Scraped Data"
    headers = ["Company Name", "Website", "Contact Number", "Address", "Description"]
    sheet.append(headers)
    for row in data:
        sheet.append(row)
    workbook.save("scraped_data.xlsx")

if __name__ == "__main__":
    BASE_URL = "https://www.yelp.com/search?find_desc=IT+Services&find_loc=San+Francisco%2C+CA"
    TOTAL_PAGES = 5
    scrape_dynamic_site(BASE_URL, TOTAL_PAGES, use_selenium=True)
