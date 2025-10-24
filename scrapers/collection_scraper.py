from scrapers.scraper import Scraper
import bs4
import logging
import random
import time
import warnings
import undetected_chromedriver as uc

# Disable all warnings
warnings.filterwarnings("ignore")
logging.getLogger('WDM').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class CollectionScraper(Scraper):
    def __init__(self, url):
        super().__init__(url)

    def get_collection_urls(self):
        """Scrape all collection URLs from the main collections page."""
        
        options = uc.ChromeOptions()
        # Run in visible mode for manual solving
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = uc.Chrome(options=options)
        
        try:
            logger.info("Opening browser to https://wiki.cs.money/collections")

            
            driver.get("https://wiki.cs.money/collections")
            import time
            time.sleep(15)
            
            # Get the page source
            html = driver.page_source
            soup = bs4.BeautifulSoup(html, "html.parser")
            
            # Find collection links
            collection_links = soup.find_all('a', class_="blzuifkxmlnzwzwpwjzrrtwcse")
            logger.info(f"Found {len(collection_links)} collection links")
            
            # Process collections
            to_remove = [
                'collection set overpass 2024',
                'collection set community 34', 
                'collection set graphic design',
                'collection set xpshop wpn 01',
                'collection set realism camo',
            ]
            
            to_adjust = {
                "operation hydra": "the operation hydra collection",
                "the x ray collection": "the x-ray collection",
            }
            
            collection_urls = {}
            for link in collection_links:
                uri = link['href']
                name = uri.replace('/collections/', '').replace('-', ' ').strip()
                
                if name not in to_remove:
                    if name in to_adjust:
                        name = to_adjust[name]
                        
                    url = "https://wiki.cs.money" + uri
                    collection_urls[name] = {'url': url, "skins": []}
                    logger.info(f"Found: {name}")
            
            logger.info(f"Successfully found {len(collection_urls)} collections!")
            
            # Save to JSON file
            import json
            with open("collection_urls.json", "w") as f:
                json.dump(collection_urls, f, indent=2)
            
            logger.info("Saved collection URLs to collection_urls.json")
            logger.info("You can now use this data in your main scraper!")
            
            return collection_urls
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {}
        finally:
            driver.quit()
    
    def get_collection_urls_with_driver(self):
        """Scrape all collection URLs from the main collections page and return driver for reuse."""
        
        options = uc.ChromeOptions()
        # Run in visible mode for manual solving
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = uc.Chrome(options=options)
        
        try:
            logger.info("Opening browser to https://wiki.cs.money/collections")
            
            driver.get("https://wiki.cs.money/collections")
            import time
            time.sleep(15)
            
            # Get the page source
            html = driver.page_source
            soup = bs4.BeautifulSoup(html, "html.parser")
            
            # Save HTML for debugging
            with open("collections_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Saved page HTML to collections_page.html")
            
            # Find collection links
            collection_links = soup.find_all('a', class_="blzuifkxmlnzwzwpwjzrrtwcse")
            logger.info(f"Found {len(collection_links)} collection links")
            
            # Process collections
            to_remove = [
                'collection set overpass 2024',
                'collection set community 34', 
                'collection set graphic design',
                'collection set xpshop wpn 01',
                'collection set realism camo',
            ]
            
            to_adjust = {
                "operation hydra": "the operation hydra collection",
                "the x ray collection": "the x-ray collection",
            }
            
            collection_urls = {}
            for link in collection_links:
                uri = link['href']
                name = uri.replace('/collections/', '').replace('-', ' ').strip()
                
                if name not in to_remove:
                    if name in to_adjust:
                        name = to_adjust[name]
                        
                    url = "https://wiki.cs.money" + uri
                    collection_urls[name] = {'url': url, "skins": []}
                    logger.info(f"Found: {name}")
            
            logger.info(f"Successfully found {len(collection_urls)} collections!")
            
            # Save to JSON file
            import json
            with open("collection_urls.json", "w") as f:
                json.dump(collection_urls, f, indent=2)
            
            logger.info("Saved collection URLs to collection_urls.json")
            logger.info("Reusing driver for individual collection pages...")
            
            return collection_urls, driver
            
        except Exception as e:
            logger.error(f"Error: {e}")
            driver.quit()
            return {}, None
    
    def scrape_one_page_with_driver(self, driver, url):
        """Scrape a single collection page using existing driver."""
        logger.info(f"Scraping collection page: {url}")
        
        try:
            driver.get(url)
            import time
            time.sleep(5)  # Shorter wait since we already solved Cloudflare
            
            # Get the page source
            html = driver.page_source
            soup = bs4.BeautifulSoup(html, "html.parser")
            
            logger.info(f"Successfully scraped page. Content length: {len(html)}")
            return soup
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return None
            
    def scrape_one_page(self, url, retries=0):
        """Scrape a single collection page."""
        logger.info(f"Scraping collection page: {url}")
        
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = uc.Chrome(options=options)
        
        try:
            driver.get(url)
            import time
            time.sleep(15)  # Give time to manually solve Cloudflare if needed
            
            # Get the page source
            html = driver.page_source
            soup = bs4.BeautifulSoup(html, "html.parser")
            
            logger.info(f"Successfully scraped page. Content length: {len(html)}")
            return soup
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return None
        finally:
            driver.quit()

    def scrape_all_pages(self, ):
        # Get collections and driver in one go
        collections, driver = self.get_collection_urls_with_driver()
        logger.info(f"Found {len(collections)} collections to scrape")

        # Load existing collections data if it exists
        import json
        import os
        
        existing_data = {}
        if os.path.exists("collections_data.json"):
            try:
                with open("collections_data.json", "r") as f:
                    existing_data = json.load(f)
                logger.info(f"Loaded existing data for {len(existing_data)} collections")
            except:
                logger.info("Starting fresh - no existing data found")

        try:
            for name, item in collections.items():
                # Skip if we already have this collection's data
                if name in existing_data and existing_data[name].get('skins'):
                    logger.info(f"Skipping {name} - already have data")
                    continue
                    
                logger.info(f"Scraping collection: {name}")
                soup = self.scrape_one_page_with_driver(driver, item['url'])
                if soup:
                    # Parse items from this collection
                    items = self.parse_items(soup)
                    
                    # Save this collection's data
                    if items:  # If we got any items
                        # Get the first (and only) collection from items
                        collection_name = list(items.keys())[0]
                        collection_items = items[collection_name]
                        
                        collection_data = {
                            'url': item['url'],
                            'skins': collection_items
                        }
                        
                        # Update existing data
                        existing_data[name] = collection_data
                        
                        # Save to file
                        with open("collections_data.json", "w") as f:
                            json.dump(existing_data, f, indent=2)
                        
                        logger.info(f"Saved {len(collection_items)} items for {name}")
                    
                    yield soup
                else:
                    logger.error(f"Failed to scrape collection: {name}")
        finally:
            # Close the driver when done
            driver.quit()
        
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
                
        logger.info(f"Successfully parsed {len(items[collection_name])} items for {collection_name}")
        return items