import pytest
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import from our updated script
from scrape_chatgpt import SeleniumScraper, ContentHandler, Config

@pytest.fixture
def config():
    """Create a test config object."""
    return Config(
        chrome_driver_path='/usr/bin/chromedriver',
        website_url='https://chat.openai.com',
        wait_timeout=10,
        repo_path='.',
        comparison_output='test_changes.json'
    )

@pytest.fixture
def content_handler(config):
    """Create a ContentHandler instance."""
    return ContentHandler(config)

@pytest.fixture
def create_test_files():
    """Create test HTML files for comparison testing."""
    # Create directory
    os.makedirs('scraped_pages', exist_ok=True)
    
    # Create yesterday file
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    yesterday_file = Path(f'scraped_pages/chat_openai_{yesterday}_120000.html')
    with open(yesterday_file, 'w') as f:
        f.write('<html><body><div>Test content</div></body></html>')
    
    # Create today file
    today = datetime.now().strftime("%Y%m%d")
    today_file = Path(f'scraped_pages/chat_openai_{today}_120000.html')
    with open(today_file, 'w') as f:
        f.write('<html><body><div>Test content updated</div></body></html>')
    
    # Return file paths for cleanup
    yield yesterday_file, today_file
    
    # Cleanup
    if yesterday_file.exists():
        os.remove(yesterday_file)
    if today_file.exists():
        os.remove(today_file)
    
    # Remove test changes file
    test_changes = Path('test_changes.json')
    if test_changes.exists():
        os.remove(test_changes)

def test_get_previous_file(content_handler, create_test_files):
    """Test getting the previous file."""
    yesterday_file, _ = create_test_files
    
    result = content_handler.get_previous_file()
    assert result is not None
    assert result.exists()

def test_compare_content(content_handler, create_test_files):
    """Test content comparison."""
    yesterday_file, today_file = create_test_files
    
    changes = content_handler.compare_content(yesterday_file, today_file)
    
    assert changes['has_changes'] is True
    assert changes['additions'] > 0
    assert 'diff_summary' in changes

@patch('scrape_chatgpt.uc.Chrome')
def test_undetected_driver_setup(mock_chrome, config):
    """Test undetected driver setup."""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    
    scraper = SeleniumScraper(config)
    driver = scraper.setup_undetected_driver()
    
    assert driver is not None
    assert mock_chrome.called

@patch('scrape_chatgpt.webdriver.Chrome')
def test_regular_driver_setup(mock_chrome, config):
    """Test regular driver setup."""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    
    scraper = SeleniumScraper(config)
    driver = scraper.setup_regular_driver()
    
    assert driver is not None
    assert mock_chrome.called

def test_config_from_env():
    """Test config loading from environment."""
    # Set test environment variables
    os.environ['CHROME_DRIVER_PATH'] = '/test/path'
    os.environ['WEBSITE_URL'] = 'https://test.com'
    os.environ['WAIT_TIMEOUT'] = '30'
    
    config = Config.from_env()
    
    assert config.chrome_driver_path == '/test/path'
    assert config.website_url == 'https://test.com'
    assert config.wait_timeout == 30