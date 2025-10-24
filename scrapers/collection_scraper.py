from scrapers.scraper import Scraper
import bs4
import logging
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class CollectionScraper(Scraper):
    def __init__(self, url):
        super().__init__(url)

    def get_collection_urls(self):
        """Scrape all collection URLs from the main collections page."""
        
        # Use Selenium to bypass Cloudflare
        options = webdriver.ChromeOptions()
        # Remove headless mode to help bypass Cloudflare
        # options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        try:
            # Now visit the collections page
            logger.info(f"Visiting URL: {self.base_url}")
            driver.get(self.base_url)
            
            # Wait for Cloudflare challenge to complete
            logger.info("Waiting for Cloudflare challenge to complete...")
            time.sleep(15)  # Wait for Cloudflare challenge
            
            # Check if we're still on Cloudflare challenge page
            current_url = driver.current_url
            logger.info(f"Current URL after loading: {current_url}")
            
            # Wait for page to fully load after Cloudflare
            time.sleep(5)
            
            # Get the page source after Cloudflare has processed
            html = driver.page_source
            soup = bs4.BeautifulSoup(html, "html.parser")
            
            
            # Find all links that contain a collection name pattern
            collection_links = soup.find_all('a', class_="blzuifkxmlnzwzwpwjzrrtwcse")
            logger.info(f"Found {len(collection_links)} links containing '/collections/'")

            to_remove = [
            'collection set overpass 2024',
            'collection set community 34',
            'collection set graphic design',
            'collection set xpshop wpn 01',
            'collection set realism camo',
            ]
            
            to_adjust = {
                "operation hydra" : "the operation hydra collection",
                "the x ray collection" : "the x-ray collection",
            }
            
            # Extract unique collection URLs
            collection_urls = {}
            for link in collection_links:
                uri = link['href']
                name = uri.replace('/collections/', '').replace('-', ' ').strip()
                if name not in to_remove:
                    if name in to_adjust:
                        name = to_adjust[name]
                        
                    url = "https://wiki.cs.money" + uri
                    collection_urls[name] = {'url': url, "skins": []}
                    logger.info(f"Found collection URL: {url}")
                
            logger.info(f"Found {len(collection_urls)} unique collection URLs")
            
            return collection_urls
            
        except Exception as e:
            logger.error(f"Error fetching collection URLs: {e}")
            return []
        finally:
            driver.quit()
            
    def scrape_one_page(self, url, retries=0):
        """Scrape a single collection page."""
        logger.info(f"Scraping collection page: {url}")
        headers = {"User-Agent": random.choice(self.user_agents)}
        response = self.session.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch collection page: {response.status_code}")
            return None
        
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        logger.info(f"Successfully scraped page. Content length: {len(response.text)}")
        return soup

    def scrape_all_pages(self, ):
        collections = self.get_collection_urls()
        logger.info(f"Found {len(collections)} collections to scrape")

        for name, item in collections.items():
            logger.info(f"Scraping collection: {name}")
            soup = self.scrape_one_page(item['url'])
            if soup:
                yield soup
            else:
                logger.error(f"Failed to scrape collection: {name}")
        
    def get_items(self, ):
        all_items = {}
        for soup in self.scrape_all_pages():
            items = self.parse_items(soup)
            # Merge the items into all_items
            for collection_name, collection_items in items.items():
                if collection_name not in all_items:
                    all_items[collection_name] = []
                all_items[collection_name].extend(collection_items)
        
        return all_items

    def parse_items(self, soup):
        items = {}
        if not soup:
            logger.error("Received empty soup in parse_items")
            return items
            
        logger.info(f"Parsing items from soup. Content length: {len(str(soup))}")
        
        try:
            collection_name = soup.find('h1', class_='rdmwocwwwyeqwxiiwtdwuwgwkh')
            if collection_name:
                collection_name = collection_name.text.strip()
                logger.info(f"Found collection name: {collection_name}")
        except Exception as e:
            logger.error("Collection name not found")
            return items
        
        # Find all item divs
        item_divs = soup.find_all('div', class_='kxmatkcipwonxvwweiqqdoumxg')
        logger.info(f"Found {len(item_divs)} item divs")
        
        for item in item_divs:
            try:
                weapon_name = item.find('div', class_='szvsuisjrrqalciyqqzoxoaubw')
                skin_name = item.find('div', class_='zhqwubnajobxbgkzlnptmjmgwn')
                rarities = item.find_all('div', class_='nwdmbwsohrhpxvdldicoixwfed')
                rarity = rarities[1]
                
                if collection_name not in items:
                    items[collection_name] = []
                
                if all([weapon_name, skin_name, rarity]):
                    items[collection_name].append({
                        'collection_name': collection_name,
                        'weapon_name': weapon_name.text.strip(),
                        'skin_name': skin_name.text.strip(),
                        'rarity': rarity.get('title', '').strip()
                    })
                    logger.info(f"Successfully parsed item: {weapon_name.text.strip()} {skin_name.text.strip()} {rarity.get('title', '').strip()}")
                else:
                    logger.warning("Missing required elements in item")
            except Exception as e:
                logger.error(f"Error parsing item: {e}")
                
        logger.info(f"Successfully parsed {len(items)} items")
        return items