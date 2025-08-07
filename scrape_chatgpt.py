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
)
from utils.logger import log


def start_driver():
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--user-agent={USER_AGENT}")
    width, height = VIEWPORT
    opts.add_argument(f"--window-size={width},{height}")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def login(driver):
    log.info("navigating to login")
    driver.get("https://chat.openai.com/auth/login")
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(
        OPENAI_USERNAME
    )
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(
        OPENAI_PASSWORD
    )
    driver.find_element(By.ID, "login").click()
    wait.until(EC.url_contains("/chat"))
    log.info("login complete")


if __name__ == "__main__":
    with start_driver() as driver:
        login(driver)
        log.info("scrape run finished ok")
