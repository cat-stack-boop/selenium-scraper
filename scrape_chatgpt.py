from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    OPENAI_USERNAME,
    OPENAI_PASSWORD,
    HEADLESS,
    USER_AGENT,
    VIEWPORT,
    Config,
)
from utils.logger import log
from login import LoginHandler, LoginConfig


def start_driver():
    cfg = Config.from_env()
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--user-agent={USER_AGENT}")
    width, height = VIEWPORT
    opts.add_argument(f"--window-size={width},{height}")
    if cfg.chrome_binary_path:
        opts.binary_location = cfg.chrome_binary_path
    if cfg.chrome_driver_path:
        service = Service(cfg.chrome_driver_path)
    else:
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def login(driver):
    """Login flow with cookie persistence and fallback to simple credential form.

    Notes:
    - Always navigates to the explicit login URL first to ensure a consistent entry point.
    - Tries loading cookies; if authenticated, returns early.
    - Falls back to the simple username/password form used in tests and basic runs.
    - Saves cookies on successful credential login.
    """
    log.info("navigating to login")
    driver.get("https://chat.openai.com/auth/login")

    # Try cookie-based auth first (no-op if cookie file doesn't exist)
    login_config = LoginConfig.from_env()
    handler = LoginHandler(driver, login_config, timeout=30)
    if login_config.use_cookies:
        try:
            if handler.load_cookies() and handler.check_login_status():
                log.info("login via cookies successful")
                return
        except Exception:
            # Best-effort cookie path; fall back silently to credential flow
            log.info("cookie-based login unavailable, falling back to credentials")

    # Fallback to simple username/password form
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(OPENAI_USERNAME)
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(OPENAI_PASSWORD)
    driver.find_element(By.ID, "login").click()
    wait.until(EC.url_contains("/chat"))
    log.info("credential login complete")

    # Persist cookies for future sessions (best-effort)
    try:
        handler.save_cookies()
    except Exception:
        pass


if __name__ == "__main__":
    with start_driver() as driver:
        login(driver)
        log.info("scrape run finished ok")
