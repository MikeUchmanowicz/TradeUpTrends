#!/usr/bin/env python3
"""
Manual Collection Scraper
Run this once to manually solve Cloudflare and save collection data
"""

import undetected_chromedriver as uc
import bs4
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_collections_manually():
    """Manually scrape collections with user solving Cloudflare"""
    
    options = uc.ChromeOptions()
    # Run in visible mode for manual solving
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = uc.Chrome(options=options)
    
    try:
        logger.info("Opening browser to https://wiki.cs.money/collections")
        logger.info("MANUAL ACTION REQUIRED:")
        logger.info("   1. Solve the Cloudflare challenge (click checkbox)")
        logger.info("   2. Wait for the collections page to load completely")
        logger.info("   3. Press ENTER in this terminal when ready")
        
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

def get_collection_data(collection_urls):
    """Get collection data from the collection URLs."""
    for collection_name, collection_data in collection_urls.items():
        url = collection_data['url']
        skins = collection_data['skins']
        print(f"Collection: {collection_name}")
        print(f"URL: {url}")
        print(f"Skins: {skins}")
        print("-" * 50)

if __name__ == "__main__":
    print("Manual Collection Scraper")
    print("=" * 50)
    collections = scrape_collections_manually()
    
    if collections:
        print(f"\nSuccess! Found {len(collections)} collections")
        print("Data saved to: collection_urls.json")
    else:
        print("\nFailed to scrape collections")
