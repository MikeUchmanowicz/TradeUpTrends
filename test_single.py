from scrapers.price_scraper import PriceScraper
from data import items_dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pagination():
    url = "https://steamcommunity.com/market/"
    price_scraper = PriceScraper(url, items_dict)
    
    weapon = "AK-47"
    logger.info(f"Testing {weapon} pagination...")
    last_page = price_scraper.get_last_page(weapon)
    logger.info(f"Found {last_page} pages for {weapon}")

    # Scrape first few pages to verify
    for i, page_soup in enumerate(price_scraper.scrape_all_pages(weapon)):
        if i >= 2: # Scrape first 3 pages
            break
        items = price_scraper.parse_items(page_soup)
        logger.info(f"Page {i+1}: Found {len(items)} items")

if __name__ == "__main__":
    test_pagination()
