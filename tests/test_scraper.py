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
        comparison_output='test_changes.json',
        chrome_binary_path='/custom/chrome/path'
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

@patch('scrape_chatgpt.uc.ChromeOptions')
@patch('scrape_chatgpt.uc.Chrome')
def test_undetected_driver_setup(mock_chrome, mock_chrome_options_uc, config):
    """Test undetected driver setup."""
    mock_driver_instance = MagicMock()
    mock_chrome.return_value = mock_driver_instance
    
    mock_options_instance = MagicMock()
    mock_chrome_options_uc.return_value = mock_options_instance
    
    scraper = SeleniumScraper(config)
    driver = scraper.setup_undetected_driver()
    
    assert driver is not None
    mock_chrome_options_uc.assert_called_once()
    mock_chrome.assert_called_once_with(options=mock_options_instance)
    assert mock_options_instance.binary_location == config.chrome_binary_path

    # Test with chrome_binary_path = None
    config.chrome_binary_path = None
    scraper_no_binary_path = SeleniumScraper(config)
    mock_options_instance_no_bp = MagicMock()
    mock_options_instance_no_bp.binary_location = None # Ensure it's not set by default
    mock_chrome_options_uc.return_value = mock_options_instance_no_bp
    
    scraper_no_binary_path.setup_undetected_driver()
    # We expect binary_location to remain None if not set in config
    assert mock_options_instance_no_bp.binary_location is None


@patch('scrape_chatgpt.webdriver.ChromeOptions')
@patch('scrape_chatgpt.webdriver.Chrome')
def test_regular_driver_setup(mock_chrome, mock_chrome_options_webdriver, config):
    """Test regular driver setup."""
    mock_driver_instance = MagicMock()
    mock_chrome.return_value = mock_driver_instance

    mock_options_instance = MagicMock()
    mock_chrome_options_webdriver.return_value = mock_options_instance

    scraper = SeleniumScraper(config)
    driver = scraper.setup_regular_driver()

    assert driver is not None
    mock_chrome_options_webdriver.assert_called_once()
    mock_chrome.assert_called_once_with(options=mock_options_instance)
    assert mock_options_instance.binary_location == config.chrome_binary_path

    # Test with chrome_binary_path = None
    config.chrome_binary_path = None
    scraper_no_binary_path = SeleniumScraper(config)
    mock_options_instance_no_bp = MagicMock()
    mock_options_instance_no_bp.binary_location = None # Ensure it's not set by default
    mock_chrome_options_webdriver.return_value = mock_options_instance_no_bp
    
    scraper_no_binary_path.setup_regular_driver()
    # We expect binary_location to remain None if not set in config
    assert mock_options_instance_no_bp.binary_location is None

# --- Tests for Login Functionality Integration ---

@patch('scrape_chatgpt.LoginHandler')
@patch('scrape_chatgpt.LoginConfig.from_env')
@patch('scrape_chatgpt.webdriver.Chrome') # Mock the driver itself
def test_login_integration_regular_driver(mock_chrome_driver, mock_login_config_from_env, mock_login_handler, config):
    """Test login handler is called in regular driver when login is configured."""
    mock_driver_instance = MagicMock()
    mock_chrome_driver.return_value = mock_driver_instance
    
    # Configure LoginConfig mock to simulate login being enabled
    mock_login_config_instance = MagicMock()
    mock_login_config_instance.username = "testuser"
    mock_login_config_instance.password = "testpass"
    mock_login_config_instance.use_cookies = True
    mock_login_config_from_env.return_value = mock_login_config_instance
    
    mock_handler_instance = MagicMock()
    mock_login_handler.return_value = mock_handler_instance
    
    scraper = SeleniumScraper(config)
    scraper.setup_regular_driver()
    
    mock_login_config_from_env.assert_called_once()
    mock_login_handler.assert_called_once_with(mock_driver_instance, mock_login_config_instance, config.wait_timeout)
    mock_handler_instance.handle_login.assert_called_once()

@patch('scrape_chatgpt.LoginHandler')
@patch('scrape_chatgpt.LoginConfig.from_env')
@patch('scrape_chatgpt.webdriver.Chrome')
def test_login_integration_regular_driver_no_login_configured(mock_chrome_driver, mock_login_config_from_env, mock_login_handler, config):
    """Test login handler is NOT called in regular driver when login is not configured."""
    mock_chrome_driver.return_value = MagicMock()
    
    # Configure LoginConfig mock to simulate login being disabled
    mock_login_config_instance = MagicMock()
    mock_login_config_instance.username = None
    mock_login_config_instance.password = None
    mock_login_config_instance.use_cookies = False
    mock_login_config_from_env.return_value = mock_login_config_instance
    
    scraper = SeleniumScraper(config)
    scraper.setup_regular_driver()
    
    mock_login_config_from_env.assert_called_once() # Still called to check
    mock_login_handler.assert_not_called()


@patch('scrape_chatgpt.LoginHandler')
@patch('scrape_chatgpt.LoginConfig.from_env')
@patch('scrape_chatgpt.uc.Chrome') # Mock the undetected driver
def test_login_integration_undetected_driver(mock_uc_chrome_driver, mock_login_config_from_env, mock_login_handler, config):
    """Test login handler is called in undetected driver when login is configured."""
    mock_driver_instance = MagicMock()
    mock_uc_chrome_driver.return_value = mock_driver_instance
    
    # Configure LoginConfig mock
    mock_login_config_instance = MagicMock()
    mock_login_config_instance.username = "testuser"
    mock_login_config_instance.password = "testpass"
    mock_login_config_instance.use_cookies = True
    mock_login_config_from_env.return_value = mock_login_config_instance
    
    mock_handler_instance = MagicMock()
    mock_login_handler.return_value = mock_handler_instance
    
    scraper = SeleniumScraper(config)
    scraper.setup_undetected_driver()
    
    mock_login_config_from_env.assert_called_once()
    mock_login_handler.assert_called_once_with(mock_driver_instance, mock_login_config_instance, config.wait_timeout)
    mock_handler_instance.handle_login.assert_called_once()

@patch('scrape_chatgpt.LoginHandler')
@patch('scrape_chatgpt.LoginConfig.from_env')
@patch('scrape_chatgpt.uc.Chrome')
def test_login_integration_undetected_driver_no_login_configured(mock_uc_chrome_driver, mock_login_config_from_env, mock_login_handler, config):
    """Test login handler is NOT called in undetected driver when login is not configured."""
    mock_uc_chrome_driver.return_value = MagicMock()
    
    # Configure LoginConfig mock
    mock_login_config_instance = MagicMock()
    mock_login_config_instance.username = None
    mock_login_config_instance.password = None
    mock_login_config_instance.use_cookies = False
    mock_login_config_from_env.return_value = mock_login_config_instance
    
    scraper = SeleniumScraper(config)
    scraper.setup_undetected_driver()
    
    mock_login_config_from_env.assert_called_once()
    mock_login_handler.assert_not_called()


def test_config_from_env(monkeypatch):
    """Test config loading from environment."""
    # Set test environment variables
    monkeypatch.setenv('CHROME_DRIVER_PATH', '/test/path')
    monkeypatch.setenv('WEBSITE_URL', 'https://test.com')
    monkeypatch.setenv('WAIT_TIMEOUT', '30')
    monkeypatch.setenv('CHROME_BINARY_PATH', '/env/chrome/path')
    
    config = Config.from_env()
    
    assert config.chrome_driver_path == '/test/path'
    assert config.website_url == 'https://test.com'
    assert config.wait_timeout == 30
    assert config.chrome_binary_path == '/env/chrome/path'

    # Test default
    monkeypatch.delenv('CHROME_BINARY_PATH', raising=False)
    config_default_binary = Config.from_env()
    assert config_default_binary.chrome_binary_path is None
