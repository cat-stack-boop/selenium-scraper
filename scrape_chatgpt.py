import os
import time
import json
import logging
import difflib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from config import Config
from login import LoginHandler, LoginConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeleniumScraper:
    def __init__(self, config: Config):
        self.config = config
        self.driver = None
    
    def setup_regular_driver(self):
        """Setup regular Chrome driver with anti-detection measures."""
        chrome_options = webdriver.ChromeOptions()
        
        # Anti-detection measures
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-infobars')
        
        # Add realistic user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Set binary location
        if self.config.chrome_binary_path:
            chrome_options.binary_location = self.config.chrome_binary_path
        
        # Additional experimental options
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.delete_all_cookies() # Ensure a clean session before login/navigation
            
            login_config = LoginConfig.from_env()
            if login_config.username or login_config.password or login_config.use_cookies:
                logger.info("Attempting login...")
                login_handler = LoginHandler(driver, login_config, self.config.wait_timeout)
                if not login_handler.handle_login():
                    logger.warning("Login failed. Proceeding without login.")
                else:
                    logger.info("Login successful or already logged in.")
            
            # Execute CDP commands to prevent detection
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup regular Chrome driver: {str(e)}")
            return None

    def setup_undetected_driver(self):
        """Setup undetected-chromedriver."""
        try:
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            if self.config.chrome_binary_path:
                chrome_options.binary_location = self.config.chrome_binary_path
            
            driver = uc.Chrome(options=chrome_options)
            driver.delete_all_cookies() # Ensure a clean session before login/navigation
            
            login_config = LoginConfig.from_env()
            if login_config.username or login_config.password or login_config.use_cookies:
                logger.info("Attempting login with undetected-chromedriver...")
                login_handler = LoginHandler(driver, login_config, self.config.wait_timeout)
                if not login_handler.handle_login():
                    logger.warning("Login failed with undetected-chromedriver. Proceeding without login.")
                else:
                    logger.info("Login successful or already logged in with undetected-chromedriver.")
            
            return driver
        except Exception as e:
            logger.error(f"Failed to setup undetected Chrome driver: {str(e)}")
            return None
    
    def wait_for_page_load(self, timeout: int = None):
        """Wait for page to load and bypass CloudFlare."""
        if timeout is None:
            timeout = self.config.wait_timeout
            
        try:
            # Initial delay for CloudFlare
            time.sleep(5)
            
            # Wait for CloudFlare to finish
            WebDriverWait(self.driver, timeout).until(
                lambda d: not any(x in d.title.lower() for x in ["just a moment", "cloudflare"])
            )
            
            # Wait for main content
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for page to be fully loaded
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Additional delay to ensure JavaScript execution
            time.sleep(5)
            
            return True
        except TimeoutException:
            logger.warning("Timeout waiting for page to load - continuing anyway")
            return True  # Continue even if timeout occurs
        except Exception as e:
            logger.error(f"Error waiting for page load: {str(e)}")
            return False
    
    def _try_with_driver(self, driver_setup_method) -> Optional[str]:
        """Try scraping with a specific driver setup method."""
        try:
            self.driver = driver_setup_method()
            if not self.driver:
                return None
                
            return self.scrape_page()
        except Exception as e:
            logger.error(f"Error with driver: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def scrape_page(self) -> Optional[str]:
        """Scrape the target page with enhanced error handling and CloudFlare bypass."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Navigate to the page
                self.driver.get(self.config.website_url)
                
                # Wait for page to load and bypass CloudFlare
                if not self.wait_for_page_load():
                    raise Exception("Failed to load page properly")
                
                # Get page source
                page_content = self.driver.page_source
                
                # Verify we got meaningful content
                if len(page_content) < 500 or "Just a moment..." in page_content:
                    retry_count += 1
                    logger.warning(f"Received CloudFlare challenge page or invalid content. Retry {retry_count}/{max_retries}")
                    time.sleep(10)  # Wait before retry
                    continue
                    
                return page_content
            except WebDriverException as e:
                retry_count += 1
                logger.warning(f"WebDriver error: {str(e)}. Retry {retry_count}/{max_retries}")
                time.sleep(10)  # Wait before retry
            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")
                return None
        
        logger.error(f"Failed to scrape page after {max_retries} retries")
        return None
    
    def run(self) -> Optional[str]:
        """Run the scraper with multiple driver attempts."""
        # Try undetected-chromedriver first
        logger.info("Attempting with undetected-chromedriver...")
        content = self._try_with_driver(self.setup_undetected_driver)
        
        # If undetected-chromedriver failed, try regular driver
        if not content:
            logger.info("Attempting with regular Chrome driver...")
            content = self._try_with_driver(self.setup_regular_driver)
        
        return content

class ContentHandler:
    def __init__(self, config: Config):
        self.config = config
    
    def save_page_content(self, content: str) -> Optional[Path]:
        """Save the scraped content to a file."""
        try:
            # Create scraped_pages directory if it doesn't exist
            output_dir = Path(self.config.repo_path) / 'scraped_pages'
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f'chat_openai_{timestamp}.html'
            
            # Save content
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved content to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            return None
    
    def get_previous_file(self) -> Optional[Path]:
        """Get the most recent file from the previous day."""
        try:
            output_dir = Path(self.config.repo_path) / 'scraped_pages'
            if not output_dir.exists():
                return None
            
            # Get all files sorted by creation time (newest first)
            files = sorted(
                [f for f in output_dir.glob('*.html')], 
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not files:
                return None
            
            # Return the most recent file
            return files[0]
        except Exception as e:
            logger.error(f"Error getting previous file: {str(e)}")
            return None
    
    def _extract_main_content(self, html: str) -> str:
        """Extract the main content from HTML to reduce noise in diff."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements that might contain changing content
            for element in soup(['script', 'style', 'noscript', 'meta', 'link']):
                element.decompose()
            
            # Extract body content
            body = soup.body
            if body:
                return str(body)
            return str(soup)
        except Exception as e:
            logger.warning(f"Error extracting main content: {str(e)}. Using full HTML.")
            return html
    
    def compare_content(self, previous_file: Path, current_file: Path) -> Dict[str, Any]:
        """Compare the current page with the previous one and detect changes."""
        try:
            # Read files
            with open(previous_file, 'r', encoding='utf-8') as f:
                previous_html = f.read()
            
            with open(current_file, 'r', encoding='utf-8') as f:
                current_html = f.read()
            
            # Extract main content to reduce noise
            previous_content = self._extract_main_content(previous_html)
            current_content = self._extract_main_content(current_html)
            
            # Calculate diff
            diff = list(difflib.unified_diff(
                previous_content.splitlines(),
                current_content.splitlines(),
                lineterm='',
                n=3
            ))
            
            # Count changes
            changes = {
                'additions': len([line for line in diff if line.startswith('+') and not line.startswith('++')]),
                'deletions': len([line for line in diff if line.startswith('-') and not line.startswith('--')]),
                'has_changes': len(diff) > 0,
                'diff_summary': '\n'.join(diff[:100]) if diff else "No changes",
                'previous_file': str(previous_file),
                'current_file': str(current_file),
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.config.comparison_output, 'w', encoding='utf-8') as f:
                json.dump(changes, f, indent=2)
            
            logger.info(f"Comparison completed. Changes: {changes['additions']} additions, {changes['deletions']} deletions")
            return changes
        except Exception as e:
            logger.error(f"Error comparing content: {str(e)}")
            # Create empty changes object
            changes = {
                'error': str(e),
                'has_changes': False,
                'timestamp': datetime.now().isoformat()
            }
            # Save to file
            with open(self.config.comparison_output, 'w', encoding='utf-8') as f:
                json.dump(changes, f, indent=2)
            return changes

def main():
    """Main execution function."""
    config = Config.from_env()
    
    # Initialize scraper
    scraper = SeleniumScraper(config)
    content_handler = ContentHandler(config)
    
    # Scrape the page
    content = scraper.run()
    
    # Save content if successful
    if content:
        current_file = content_handler.save_page_content(content)
        if current_file:
            logger.info("Scraping completed successfully")
            
            # Compare with previous file
            previous_file = content_handler.get_previous_file()
            if previous_file and previous_file != current_file:
                changes = content_handler.compare_content(previous_file, current_file)
                return True, changes.get('has_changes', False)
            return True, False
    
    logger.error("All scraping attempts failed")
    return False, False

if __name__ == "__main__":
    success, has_changes = main()
    exit(0 if success else 1)