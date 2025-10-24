import mysql.connector
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="tut"
        )
        self.cursor = self.conn.cursor()


    def delete_all_items(self):
        """Delete all items from the weapons table."""
        logger.info("Deleting all items from the database...")

        try:
            self.cursor.execute("DELETE FROM weapons")
            self.conn.commit()
            logger.info(f"Deleted {self.cursor.rowcount} rows from the database.")
        except Exception as e:
            logger.error(f"Error deleting items: {e}")
            self.conn.rollback()
        finally:
            self.cursor.close()
            self.conn.close()

    def create_items(self, weapon, items):
        logger.info(f"Creating {len(items)} items for {weapon}...")

        try:
            # Define SQL insert command
            command = """
            INSERT IGNORE INTO weapons (weapon_name, skin_name, price, wear, is_stattrak, is_souvenir)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            # Insert each scraped item
            for item in items:
                self.cursor.execute(command, (
                    weapon,         # Weapon name
                    item["name"],   # Skin name
                    item["price"],  # Price
                    item["wear"],   # Wear condition
                    item["stat"],   # Stattrak boolean
                    item["souv"]    # Souvenir boolean
                ))

                self.conn.commit()
                logger.info(f"Inserted {self.cursor.rowcount} rows for {weapon}.")
                
        except Exception as e:
            logger.error(f"Error creating items for {weapon}: {e}")
            self.conn.rollback()
        finally:
            self.cursor.close()
            self.conn.close()
            
    def create_collection(self, collection_name):
        logger.info(f"Creating collection {collection_name}...")

        try:
            self.cursor.execute("INSERT INTO collections (name) VALUES (%s) RETURNING id", (collection_name,))
            collection_id = self.cursor.fetchone()[0]
            self.conn.commit()
            logger.info(f"Created collection {collection_name} with ID {collection_id}.")
            return collection_name, collection_id
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            self.conn.rollback()
            return None
            
            
    def create_collection_items(self, collection_name, collection_id, items):
        logger.info(f"Creating {len(items)} items for {collection_name}...")

        try:
            # Define SQL insert command
            command = """
            INSERT IGNORE INTO collection_items (collection_id, weapon_name, skin_name, rarity)
            VALUES (%s, %s, %s, %s)
            """

            # Insert each scraped item
            for item in items:
                self.cursor.execute(command, (
                    collection_id,
                    item["weapon_name"],
                    item["skin_name"],
                    item["rarity"]
                ))      

                self.conn.commit()
                logger.info(f"Inserted {self.cursor.rowcount} rows for {collection_name}.")
                
        except Exception as e:
            logger.error(f"Error creating items for {collection_name}: {e}")
            self.conn.rollback()

