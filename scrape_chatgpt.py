import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class Config:
    chrome_driver_path: str
    website_url: str
    wait_timeout: int
    repo_path: str
    comparison_output: str

def load_config() -> Config:
    """Load configuration from environment variables."""
    load_dotenv()
    return Config(
        chrome_driver_path=os.getenv('CHROME_DRIVER_PATH', ''),
        website_url=os.getenv('WEBSITE_URL', 'https://chat.openai.com'),
        wait_timeout=int(os.getenv('WAIT_TIMEOUT', '20')),
        repo_path=os.getenv('REPO_PATH', '.'),
        comparison_output=os.getenv('COMPARISON_OUTPUT', 'changes.json')
    )

def setup_regular_driver(config: Config):
    """Setup regular Chrome driver with anti-detection measures."""
    chrome_options = webdriver.ChromeOptions()
    
    # Anti-detection measures
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-infobars')
    
    # Add realistic user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Additional experimental options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Execute CDP commands to prevent detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        logging.error(f"Failed to setup regular Chrome driver: {str(e)}")
        return None

def setup_undetected_driver(config: Config):
    """Setup undetected-chromedriver."""
    try:
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = uc.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to setup undetected Chrome driver: {str(e)}")
        return None

def wait_for_page_load(driver, timeout: int = 30):
    """Wait for page to load and bypass CloudFlare."""
    try:
        # Wait for CloudFlare to finish
        WebDriverWait(driver, timeout).until(
            lambda d: not "Just a moment..." in d.title
        )
        
        # Wait for main content
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional delay to ensure JavaScript execution
        time.sleep(5)
        
        return True
    except TimeoutException:
        logging.error("Timeout waiting for page to load")
        return False
    except Exception as e:
        logging.error(f"Error waiting for page load: {str(e)}")
        return False

def scrape_page(driver, config: Config) -> Optional[str]:
    """Scrape the target page with enhanced error handling and CloudFlare bypass."""
    try:
        # Clear cookies and cache
        driver.delete_all_cookies()
        
        # Navigate to the page
        driver.get(config.website_url)
        
        # Wait for page to load and bypass CloudFlare
        if not wait_for_page_load(driver):
            raise Exception("Failed to load page properly")
        
        # Get page source
        page_content = driver.page_source
        
        # Verify we got meaningful content
        if len(page_content) < 100 or "Just a moment..." in page_content:
            raise Exception("Received CloudFlare challenge page or invalid content")
            
        return page_content
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
        return None

def save_page_content(content: str, config: Config):
    """Save the scraped content to a file."""
    try:
        # Create scraped_pages directory if it doesn't exist
        output_dir = Path(config.repo_path) / 'scraped_pages'
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f'chat_openai_{timestamp}.html'
        
        # Save content
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Saved content to {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error saving content: {str(e)}")
        return None

def main():
    """Main execution function with multiple driver attempts."""
    config = load_config()
    content = None
    
    # Try undetected-chromedriver first
    logging.info("Attempting with undetected-chromedriver...")
    driver = setup_undetected_driver(config)
    if driver:
        try:
            content = scrape_page(driver, config)
        finally:
            driver.quit()
    
    # If undetected-chromedriver failed, try regular driver
    if not content:
        logging.info("Attempting with regular Chrome driver...")
        driver = setup_regular_driver(config)
        if driver:
            try:
                content = scrape_page(driver, config)
            finally:
                driver.quit()
    
    # Save content if successful
    if content:
        saved_file = save_page_content(content, config)
        if saved_file:
            logging.info("Scraping completed successfully")
            return True
    
    logging.error("All scraping attempts failed")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
