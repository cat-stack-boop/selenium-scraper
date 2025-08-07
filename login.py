import time
import logging
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

@dataclass
class LoginConfig:
    """Configuration for login process."""
    username: Optional[str] = None
    password: Optional[str] = None
    base_url: str = "https://chat.openai.com"
    cookies_path: str = "cookies.json"
    use_cookies: bool = True
    
    @classmethod
    def from_env(cls) -> 'LoginConfig':
        """Load login configuration from environment variables."""
        return cls(
            username=os.getenv('OPENAI_USERNAME'),
            password=os.getenv('OPENAI_PASSWORD'),
            base_url=os.getenv('WEBSITE_URL', 'https://chat.openai.com'),
            cookies_path=os.getenv('COOKIES_PATH', 'cookies.json'),
            use_cookies=os.getenv('USE_COOKIES', 'true').lower() == 'true'
        )

class LoginHandler:
    """Handle login process for ChatGPT."""
    
    def __init__(self, driver, config: LoginConfig, timeout: int = 60):
        self.driver = driver
        self.config = config
        self.timeout = timeout
    
    def save_cookies(self) -> bool:
        """Save cookies to a file for future sessions."""
        try:
            cookies = self.driver.get_cookies()
            if not cookies:
                logger.warning("No cookies to save")
                return False
                
            cookies_path = Path(self.config.cookies_path)
            # Create parent directory if it doesn't exist
            cookies_path.parent.mkdir(exist_ok=True, parents=True)
            
            import json
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f)
                
            logger.info(f"Cookies saved to {cookies_path}")
            return True
        except Exception:
            logger.exception("Error saving cookies")
            return False
    
    def load_cookies(self) -> bool:
        """Load cookies from a file."""
        try:
            cookies_path = Path(self.config.cookies_path)
            if not cookies_path.exists():
                logger.warning(f"Cookies file not found: {cookies_path}")
                return False
                
            import json
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)

            if not cookies:
                logger.warning("No cookies found in file")
                return False

        # Navigate to the base URL before adding cookies
        self.driver.get(self.config.base_url)
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Add cookies to driver after navigation completes
        for cookie in cookies:
            # Some cookies might cause issues if they have expiration in the past
            if 'expiry' in cookie:
                del cookie['expiry']
            self.driver.add_cookie(cookie)

        logger.info(f"Cookies loaded from {cookies_path}")
        return True
        except Exception:
            logger.exception("Error loading cookies")
            return False
    
    def check_login_status(self) -> bool:
        """Check if we're logged in to ChatGPT."""
        try:
            # Refresh page to apply cookies
            self.driver.refresh()
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for login elements vs. logged in elements
            login_button = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Log in')]")
            if login_button:
                logger.info("Not logged in - login button detected")
                return False
                
            # Check for elements that indicate we're logged in
            try:
                # Look for elements that would be present when logged in
                # This could be a profile menu, new chat button, etc.
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'user-menu') or contains(@aria-label, 'User menu')]"))
                )
                logger.info("Successfully logged in")
                return True
            except TimeoutException:
                logger.info("No user menu found, might not be logged in")
                return False
                
        except Exception:
            logger.exception("Error checking login status")
            return False
    
    def perform_login(self) -> bool:
        """Perform login using provided credentials."""
        if not self.config.username or not self.config.password:
            logger.warning("Username or password not provided")
            return False
            
        try:
            # Find and click login button
            login_button = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')]"))
            )
            login_button.click()
            
            # Wait for login form to appear
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter username
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(self.config.username)
            
            # Click continue
            continue_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
            continue_button.click()
            
            # Wait for password field
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.config.password)
            
            # Click login
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            
            # Wait for successful login
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'user-menu') or contains(@aria-label, 'User menu')]") )
            )
            
            # Check if logged in
            return self.check_login_status()
        except Exception:
            logger.exception("Error during login process")
            return False
    
    def handle_login(self) -> bool:
        """Main method to handle the login process."""
        # First try cookies if enabled
        if self.config.use_cookies:
            logger.info("Attempting login with cookies")
            if self.load_cookies() and self.check_login_status():
                logger.info("Successfully logged in with cookies")
                return True
                
        # If cookies failed or not enabled, try credentials
        if self.config.username and self.config.password:
            logger.info("Attempting login with credentials")
            if self.perform_login():
                # Save cookies for future sessions
                self.save_cookies()
                return True
                
        logger.warning("All login attempts failed")
        return False
