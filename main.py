from scraper import Scraper
from temp import items_dict
from db import connect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    url = "https://steamcommunity.com/market/"
    scraper = Scraper(url, items_dict)

    for weapon in items_dict:
        logger.info(f"Scraping {weapon}...")
        
        # Scrape data
        items = scraper.get_items(weapon)
        
        if not items:  # Prevent errors if no items are returned
            logger.warning(f"No items found for {weapon}. Skipping...")
            continue
        
        logger.info(f"Scraped {len(items)} items for {weapon}. Connecting to database...")
        conn = connect()
        cursor = conn.cursor()

        # Define SQL insert command
        command = """
        INSERT INTO weapons (weapon_name, skin_name, price, wear, is_stattrak, is_souvenir)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Insert each scraped item
        for item in items:
            cursor.execute(command, (
                weapon,         # Weapon name
                item["name"],   # Skin name
                item["price"],  # Price
                item["wear"],   # Wear condition
                item["stat"],   # Stattrak boolean
                item["souv"]    # Souvenir boolean
            ))

        conn.commit()
        logger.info(f"Inserted {cursor.rowcount} rows for {weapon}.")
        
        # Close database connection
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
