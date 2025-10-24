import re
import time
import random
import bs4
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from scrapers.scraper import Scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceScraper(Scraper):
    
    def __init__(self, url, items_dict):
        super().__init__(url)
        self.items_dict = items_dict

    def scrape_one_page(self, weapon, index, last_page, retries=0):
        page = f"{self.base_url}{self.items_dict[weapon]}&appid=730&sort_column=price&sort_dir=asc&start={(index)*10}&count=10"
        logger.info(f"Scraping {weapon} [{index}/{last_page}]: start={(index-1)*10}&count=10")

        headers = {"User-Agent": random.choice(self.user_agents)}
        response = self.session.get(page, headers=headers)

        if response.status_code == 429:
            if retries >= 10:
                logger.error("Maximum retries reached. Aborting.")
                return None

            logger.warning(f"Rate-limited. Attempting to switch VPN...")

            # Try to switch VPN, but continue even if it fails
            vpn_switched = self.switch_mullvad_server()
            if not vpn_switched:
                logger.warning("VPN switch failed, continuing with current connection")

            return self.scrape_one_page(weapon, index, last_page, retries + 1)  

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        return soup

    def get_last_page(self, weapon, retries=0):
        # Use Selenium to load the first page
        page = f"{self.base_url}{self.items_dict[weapon]}&appid=730&sort_column=price&sort_dir=asc"
        logger.info(f"Loading first page with Selenium: {page}")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--log-level=3")  # Disable Chrome logs
        options.add_argument("--disable-logging")
        options.add_argument("--disable-dev-shm-usage")
        # Speed optimizations
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")  # Don't load images
        #options.add_argument("--disable-javascript")  # Disable JS if not needed
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-extensions")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        soup = None

        try:
            driver.get(page)
            # Wait for pagination elements to appear
            WebDriverWait(driver, 30).until(
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

            # If no pagination found, try VPN switch and retry
            logger.warning(f"No pagination found for {weapon}, trying VPN switch... (attempt {retries + 1})")
            vpn_switched = self.switch_mullvad_server()
            if vpn_switched:
                logger.info(f"Retrying get_last_page() for {weapon} after VPN switch...")
                return self.get_last_page(weapon, retries + 1)
            
            logger.error(f"No pagination found for {weapon} after VPN switch, retrying...")
            return self.get_last_page(weapon, retries + 1)
        except TimeoutException:
            logger.error("Timeout while waiting for the pagination element.")
            # Try to get page count from page source anyway
            try:
                html = driver.page_source
                soup = bs4.BeautifulSoup(html, "html.parser")
                pagination = soup.find_all('span', class_='market_paging_pagelink')
                if pagination:
                    last_page = pagination[-1].text
                    last = int(last_page)
                    logger.info(f"Found {last} pages despite timeout")
                    return last
            except:
                pass
            
            # If we still can't find pagination, try switching VPN and retrying
            logger.warning(f"Failed to get pagination for {weapon}, trying VPN switch... (attempt {retries + 1})")
            vpn_switched = self.switch_mullvad_server()
            if vpn_switched:
                logger.info(f"Retrying get_last_page() for {weapon} after VPN switch...")
                return self.get_last_page(weapon, retries + 1)  # Retry after switching VPN
            
            logger.error(f"Failed to get pagination for {weapon} after VPN switch, retrying...")
            return self.get_last_page(weapon, retries + 1)  # Keep retrying
        except Exception as e:
            logger.error(f"Failed to load page: {e}")

            # Switch Mullvad location if request fails
            logger.warning(f"Failed to load page for {weapon}, trying VPN switch... (attempt {retries + 1})")
            switched = self.switch_mullvad_server()
            if switched:
                logger.info(f"Retrying get_last_page() after switching VPN location...")
                return self.get_last_page(weapon, retries + 1)  # Retry after switching location

            logger.error(f"Failed to load page for {weapon} after VPN switch, retrying...")
            return self.get_last_page(weapon, retries + 1)  # Keep retrying
        finally:
            driver.quit()
            
            # Only try to access soup if it was successfully created
            if soup:
                pagination = soup.find_all('span', class_='market_paging_pagelink')
                if pagination:
                    last_page = pagination[-1].text
                    last = int(last_page)
                    return last
            
            return 1

    def scrape_all_pages(self, weapon):
        last_page = self.get_last_page(weapon)
        logger.info(f"Starting to scrape {last_page} pages for {weapon}")
        
        for index in range(1, last_page + 1):
            soup = self.scrape_one_page(weapon, index, last_page)
            if soup is None:
                logger.error(f"Failed to scrape page {index} for {weapon}")
                continue
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
                
                obj = {
                    "name": name,
                    "price": price,
                    "stat": stat,
                    "souv": souv,
                    "wear": wear,
                    "page": page_index,
                    "item": item_index,
                }
                page_objs.append(obj)
                
            all_objs.extend(page_objs)
            
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
        price = price.replace("usd", "")
        price = price.replace("USD", "")
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