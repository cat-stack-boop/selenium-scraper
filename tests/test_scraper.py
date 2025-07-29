from pathlib import Path
from unittest.mock import MagicMock
import importlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
import scrape_chatgpt


class DummyWait:
    def __init__(self, driver, timeout):
        self.driver = driver

    def until(self, condition):
        return MagicMock()


def test_headless_parsing(monkeypatch):
    monkeypatch.setenv("HEADLESS", "no")
    importlib.reload(config)
    assert config.HEADLESS is False


def test_login_stub(monkeypatch):
    html = Path("tests/fixtures/login.html").read_text()
    driver = MagicMock()

    def fake_get(url):
        driver.current_url = url
        driver.page_source = html

    driver.get.side_effect = fake_get
    driver.find_element.return_value = MagicMock()
    monkeypatch.setattr(scrape_chatgpt, "WebDriverWait", DummyWait)

    scrape_chatgpt.login(driver)
    assert driver.current_url.endswith("/auth/login")
