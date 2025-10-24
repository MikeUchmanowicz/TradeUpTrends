from scrapers.collection_scraper import CollectionScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_collection_scraper():
    url = "https://wiki.cs.money/collections"
    scraper = CollectionScraper(url)
    
    collections = scraper.get_collections()
    logger.info(f"Found {len(collections)} collections")
    
    for i, collection in enumerate(collections[:5]):  # Show first 5
        logger.info(f"Collection {i+1}: {collection}")

if __name__ == "__main__":
    test_collection_scraper()
