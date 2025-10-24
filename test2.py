from scrapers.price_scraper import PriceScraper
from data import items_dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_weapon():
    url = "https://steamcommunity.com/market/"
    price_scraper = PriceScraper(url, items_dict)
    
    weapon = "AK-47"
    logger.info(f"Testing {weapon}...")
    items = price_scraper.get_items(weapon)
    logger.info(f"Found {len(items)} items for {weapon}")

if __name__ == "__main__":
    test_single_weapon()
