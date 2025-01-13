import pytest
from scrape_chatgpt import compare_pages, get_yesterday_file
import os
from datetime import datetime, timedelta

def test_get_yesterday_file():
    # Create a mock file
    os.makedirs('scraped_pages', exist_ok=True)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    mock_file = f'scraped_pages/chat_openai_{yesterday}_120000.html'
    with open(mock_file, 'w') as f:
        f.write('<html></html>')
        
    result = get_yesterday_file()
    assert result == mock_file
    
    # Cleanup
    os.remove(mock_file) 