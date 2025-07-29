import pytest, scrape_chatgpt
from contextlib import contextmanager


@contextmanager
def browser():
    drv = scrape_chatgpt.start_driver()
    try:
        yield drv
    finally:
        drv.quit()


def test_login():
    with browser() as driver:
        scrape_chatgpt.login(driver)
        assert "chat.openai.com/chat" in driver.current_url

# future: mock HTML fixtures & verify diff cleaning logic

