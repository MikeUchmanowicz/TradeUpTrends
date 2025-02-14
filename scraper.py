import re
import time
import random
import requests
import bs4
import json
import logging
import pprint
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import subprocess
from collections import deque
from selenium.common.exceptions import TimeoutException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, url, items_dict):
        self.base_url = url
        self.items_dict = items_dict
        self.session = requests.Session()

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ]
        
        self.MULLVAD_PATH = r"C:\Program Files\Mullvad VPN\resources\mullvad.exe"
        self.MULLVAD_LOCATIONS = ["qas", "atl", "bos", "chi", "dal", "den", "det", "hou", "lax",
                                "txc", "mia", "nyc", "phx", "rag", "slc", "sjc", "sea", "uyk", "was"]
        self.USED_LOCATIONS = deque(maxlen=10)

    def get_ip(self):
        try:
            response = self.session.get("https://api64.ipify.org?format=json")
            return response.json().get("ip", "Unknown")
        except:
            return "Failed to fetch IP"

    def switch_mullvad_server(self):
        # Get a list of available locations (excluding last 5 used)
        available_locations = [loc for loc in self.MULLVAD_LOCATIONS if loc not in self.USED_LOCATIONS]

        # Pick a new location that hasn't been used recently
        new_loc = random.choice(available_locations)
        logger.info(f"Switching Mullvad VPN server to {new_loc}...")

        try: 
            # Set the Mullvad VPN location
            result = subprocess.run([self.MULLVAD_PATH, "relay", "set", "location", "us", new_loc], capture_output=True, text=True, check=True)
            logger.info(f"Relay Set Output: {result.stdout.strip()}")
            # Connect to Mullvad VPN
            result = subprocess.run([self.MULLVAD_PATH, "connect"], capture_output=True, text=True, check=True)
            logger.info(f"Connect Output: {result.stdout.strip()}")
            # Wait for VPN to stabilize
            time.sleep(5)
            logger.info(f"VPN switched to {new_loc}, recent history: {list(self.USED_LOCATIONS)}")
            self.USED_LOCATIONS.append(new_loc)
            return True

        except Exception as e:
            logger.error(f"Error switching Mullvad server: {e}")
            return False
    
    def scrape_one_page(self, weapon, index, retries=0):
        page = f"{self.base_url}{self.items_dict[weapon]}&sort_column=price&sort_dir=asc&start={(index-1)*10}&count=10"
        logger.info(f"Scraping page: {page}")

        headers = {"User-Agent": random.choice(self.user_agents)}
        response = self.session.get(page, headers=headers)

        if response.status_code == 429:
            if retries >= 10:
                logger.error("Maximum retries reached. Aborting.")
                return None

            logger.warning(f"Rate-limited. Retrying in 5 seconds...")
            self.switch_mullvad_server()  # Switch VPN if rate-limited

            return self.scrape_one_page(weapon, index, retries + 1)  

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        return soup


    def get_last_page(self, weapon):
        # Use Selenium to load the first page
        page = self.base_url + self.items_dict[weapon] + f"#p{1}_price_asc"
        logger.info(f"Loading first page with Selenium: {page}")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        try:
            driver.get(page)
            # Wait for pagination elements to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'market_paging_pagelink'))
            )

            html = driver.page_source
            soup = bs4.BeautifulSoup(html, "html.parser")

            # Get the last page number
            pagination = soup.find_all('span', class_='market_paging_pagelink')
            if pagination:
                last_page = pagination[-1].text
                last = int(last_page)
                return last

            return 1
        except TimeoutException:
            print("[ERROR] Timeout while waiting for the pagination element.")
            driver.quit()
            return None  # Exit early to prevent using `soup` without a value
        except Exception as e:
            logger.error(f"Failed to load page: {e}")

            # Switch Mullvad location if request fails
            switched = self.switch_mullvad_server()
            if switched:
                logger.info("Retrying get_last_page() after switching VPN location...")
                return self.get_last_page(weapon)  # Retry after switching location

            return 1  # Return default if VPN switch also fails

        finally:
            driver.quit()
            
            pagination = soup.find_all('span', class_='market_paging_pagelink')
            if pagination:
                last_page = pagination[-1].text
                last = int(last_page)
                return last
            
            return 1

    def scrape_all_pages(self, weapon):
        index = 0
        last_page = 2
        while index < last_page:
            index += 1

            if index == 1:
                last_page = self.get_last_page(weapon)
        
            soup = self.scrape_one_page(weapon, index)
            
            yield soup

    def get_items(self, weapon):
        logger.info(f"Scraping items for {weapon}")
        all_objs = []
        page_index = 0
        item_index = 0
        for page in self.scrape_all_pages(weapon):
            page_index += 1
            page_objs = []
            names = page.find_all('span', class_='market_listing_item_name')
            prices = page.find_all('span', class_='normal_price')
            
            for name, price in zip(names, prices):
                item_index += 1
                name, stat, souv, wear = self.clean_name(name)
                price = self.clean_price(price)
                
                obj = {"name":name, "price": price, "stat": stat, "souv": souv, "wear": wear, "page": page_index, "item": item_index}
                page_objs.append(obj)
                
            pprint.pprint(page_objs)
            all_objs.extend(page_objs)
            
            with open("items.json", "w") as f:
                #append to file
                obj = {f"{weapon}": all_objs}
                json.dump(obj, f, indent=4)
            
        return all_objs
    
    def clean_name(self, name):
        name = name.text.strip()
        stat = self.check_stattrak(name)
        souv = self.check_souvenir(name)
        wear = self.check_wear(name)
        
        if stat:
            name = name.replace("StatTrak™ ", "")
        if souv:
            name = name.replace("Souvenir ", "")
        if wear:
            name = name.replace(f"({wear})", "")
        
        name = name.strip()
        return name, stat, souv, wear

    def clean_price(self, price):
        price = price.text.strip()
        price = price.split('\n')[1].strip() if '\n' in price else price
        price = price.replace("$", "").replace(",", "")
        price = float(price)
        return price

    def check_wear(self, name):
        wear = re.search(r'\((.*?)\)', name)
        if wear:
            return wear.group(1)
        return None

    def check_souvenir(self, name):
        if "Souvenir" in name:
            return True
        return False

    def check_stattrak(self, name):
        if "StatTrak" in name:
            return True
        return False