from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from functools import wraps
from dotenv import load_dotenv
import logging
import os
import datetime
import subprocess
import time
import difflib
import json
from typing import Dict, Tuple, Optional, List, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Configuration
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', '/usr/bin/chromedriver')
WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://chat.openai.com')
WAIT_TIMEOUT = int(os.getenv('WAIT_TIMEOUT', 20))
REPO_PATH = os.getenv('REPO_PATH', '.')
COMPARISON_OUTPUT = os.getenv('COMPARISON_OUTPUT', 'changes.json')

def retry_on_exception(retries=3, delay=1):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        raise
                    logging.warning(f"Attempt {i+1} failed: {e}")
                    time.sleep(delay * (i + 1))
            return None
        return wrapper
    return decorator

@retry_on_exception(retries=3)
def scrape_and_save(url: str, output_file: str) -> bool:
    """
    Scrape the given URL and save the page source to a file.
    
    Args:
        url: The URL to scrape
        output_file: Path to save the scraped content
        
    Returns:
        bool: True if successful, False otherwise
    """
    driver = None
    try:
        # Set up Selenium with Chrome in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Initialize WebDriver
        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        try:
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            logging.error(f"Timeout waiting for page to load: {url}")
            return False
            
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Save the page source to a file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(soup.prettify())
        logging.info(f"Page source saved to: {output_file}")
        return True
        
    except WebDriverException as e:
        logging.error(f"WebDriver error occurred: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during scraping: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def commit_changes(repo_path: str, commit_message: str) -> bool:
    """
    Commit and push changes to git repository.
    
    Args:
        repo_path: Path to the git repository
        commit_message: Commit message
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        current_dir = os.getcwd()
        os.chdir(repo_path)
        
        # Check if there are changes to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        )
        
        if not status.stdout.strip():
            logging.info("No changes to commit")
            return True
            
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("Successfully committed and pushed changes")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False
    finally:
        os.chdir(current_dir)

def get_yesterday_file() -> Optional[str]:
    """Find the most recent file from yesterday."""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y%m%d")
    
    if not os.path.exists('scraped_pages'):
        return None
        
    files = [f for f in os.listdir('scraped_pages') if f.startswith('chat_openai_')]
    yesterday_files = [f for f in files if yesterday_str in f]
    
    return os.path.join('scraped_pages', sorted(yesterday_files)[-1]) if yesterday_files else None

def compare_pages(old_file: str, new_file: str) -> Dict[str, List[str]]:
    """
    Compare two HTML files and identify changes.
    
    Args:
        old_file: Path to yesterday's HTML file
        new_file: Path to today's HTML file
        
    Returns:
        Dict containing changes found
    """
    try:
        # Read both files
        with open(old_file, 'r', encoding='utf-8') as f:
            old_soup = BeautifulSoup(f.read(), 'html.parser')
        with open(new_file, 'r', encoding='utf-8') as f:
            new_soup = BeautifulSoup(f.read(), 'html.parser')
            
        changes = {
            'new_features': [],
            'removed_features': [],
            'modified_elements': [],
            'feature_flags': []
        }
        
        # Compare feature flags (assuming they're in data attributes or specific elements)
        old_flags = old_soup.find_all(attrs={'data-feature': True})
        new_flags = new_soup.find_all(attrs={'data-feature': True})
        
        old_flag_set = {flag.get('data-feature') for flag in old_flags}
        new_flag_set = {flag.get('data-feature') for flag in new_flags}
        
        changes['feature_flags'] = list(new_flag_set - old_flag_set)
        
        # Compare visible elements
        old_elements = old_soup.find_all(['div', 'button', 'a'])
        new_elements = new_soup.find_all(['div', 'button', 'a'])
        
        old_text = {elem.get_text().strip() for elem in old_elements if elem.get_text().strip()}
        new_text = {elem.get_text().strip() for elem in new_elements if elem.get_text().strip()}
        
        changes['new_features'] = list(new_text - old_text)
        changes['removed_features'] = list(old_text - new_text)
        
        # Save changes to file
        with open(COMPARISON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(changes, f, indent=2)
            
        logging.info(f"Comparison results saved to {COMPARISON_OUTPUT}")
        return changes
        
    except Exception as e:
        logging.error(f"Error comparing pages: {e}")
        return {}

def main():
    """Main execution function."""
    try:
        TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
        OUTPUT_FILE = f"scraped_pages/chat_openai_{TIMESTAMP}.html"
        
        if not scrape_and_save(WEBSITE_URL, OUTPUT_FILE):
            logging.error("Scraping failed")
            return
            
        # Find yesterday's file and compare
        yesterday_file = get_yesterday_file()
        if yesterday_file:
            changes = compare_pages(yesterday_file, OUTPUT_FILE)
            if changes:
                logging.info("Changes detected:")
                for category, items in changes.items():
                    if items:
                        logging.info(f"\n{category.replace('_', ' ').title()}:")
                        for item in items:
                            logging.info(f"- {item}")
        else:
            logging.info("No previous file found for comparison")
            
        if not commit_changes(REPO_PATH, f"Update scraped page at {TIMESTAMP}"):
            logging.error("Git operations failed")
            return
            
        logging.info("Script completed successfully")
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
