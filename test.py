from scrapers.collection_scraper import CollectionScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_collection_scraper():
    url = "https://wiki.cs.money/collections"
    scraper = CollectionScraper(url)
    
    collections = scraper.get_items()
    logger.info(f"Found {len(collections)} collections")
    
    for i, (collection_name, items) in enumerate(list(collections.items())[:5]):  # Show first 5
        logger.info(f"Collection {i+1}: {collection_name} ({len(items)} items)")

if __name__ == "__main__":
    test_collection_scraper()
