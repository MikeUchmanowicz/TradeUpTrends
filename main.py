from scrapers.price_scraper import PriceScraper
from scrapers.collection_scraper import CollectionScraper

from data import items_dict
from db import Database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    url = "https://steamcommunity.com/market/"
    price_scraper = PriceScraper(url, items_dict)
    collection_scraper = CollectionScraper(url)
    
    # Create database instance
    db = Database()
    
    # Delete all existing items
    db.delete_all_items()

    # Process each weapon
    for weapon in items_dict:
        logger.info(f"Scraping {weapon}...")
        items = price_scraper.get_items(weapon)
        db.create_items(weapon, items)
    

if __name__ == "__main__":
    main()
