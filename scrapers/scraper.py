import random
import requests
import time
import bs4
import subprocess
import os
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self, url):
        self.base_url = url

        self.session = requests.Session()

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ]
        
        self.MULLVAD_PATH = r"C:\Program Files\Mullvad VPN\resources\mullvad.exe"
        self.MULLVAD_LOCATIONS = ["qas", "atl", "bos", "chi", "dal", "den", "hou", "mkc", "lax",
                                "txc", "mia", "nyc", "phx", "rag", "slc", "sjc", "sea", "uyk", "was"]
        self.USED_LOCATIONS = deque(maxlen=15)

    def get_ip(self):
        try:
            response = self.session.get("https://api64.ipify.org?format=json")
            return response.json().get("ip", "Unknown")
        except:
            return "Failed to fetch IP"

    def switch_mullvad_server(self):
        # Check if Mullvad executable exists
        if not os.path.exists(self.MULLVAD_PATH):
            logger.warning(f"Mullvad executable not found at {self.MULLVAD_PATH}")
            return False
            
        # Get a list of available locations (excluding last 5 used)
        available_locations = [loc for loc in self.MULLVAD_LOCATIONS if loc.upper() not in self.USED_LOCATIONS]
        
        if not available_locations:
            logger.warning("No available VPN locations, resetting history")
            self.USED_LOCATIONS.clear()
            available_locations = self.MULLVAD_LOCATIONS

        # Pick a new location that hasn't been used recently
        new_loc = random.choice(available_locations)
        logger.info(f"Switching Mullvad VPN server to {new_loc.upper()}...")

        try: 
            # Set the Mullvad VPN location
            result = subprocess.run([self.MULLVAD_PATH, "relay", "set", "location", "us", new_loc], 
                                 capture_output=True, text=True, check=True, timeout=30)
            logger.info(f"Relay Set Output: {result.stdout.strip()} {new_loc.upper()}")
            
            # Connect to Mullvad VPN
            result = subprocess.run([self.MULLVAD_PATH, "connect"], 
                                 capture_output=True, text=True, check=True, timeout=30)
            logger.info(f"Connect Output: {result.stdout.strip()} {new_loc.upper()}")
            
            timeout = 5
            logger.info(f"Waiting {timeout} seconds for VPN to stabilize...")
            time.sleep(timeout)
            
            current_ip = self.get_ip()

            logger.info(f"VPN switched to {new_loc.upper()}, IP: {current_ip}, recent history: {list(self.USED_LOCATIONS)}")
            self.USED_LOCATIONS.append(new_loc.upper())

            return True

        except subprocess.TimeoutExpired:
            logger.error("VPN switch timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"VPN command failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error switching Mullvad server: {e}")
            return False

    def scrape_one_page(self, weapon, index, last_page, retries=0):
        raise NotImplementedError("Subclasses must implement scrape_one_page")

    def get_last_page(self, weapon):
        raise NotImplementedError("Subclasses must implement get_last_page")

    def scrape_all_pages(self, weapon):
        raise NotImplementedError("Subclasses must implement scrape_all_pages")

    def get_items(self, weapon):
        raise NotImplementedError("Subclasses must implement get_items")