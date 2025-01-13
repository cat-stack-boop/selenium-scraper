from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class Config:
    chrome_driver_path: str
    website_url: str
    wait_timeout: int
    repo_path: str
    comparison_output: str
    
    @classmethod
    def from_env(cls) -> 'Config':
        load_dotenv()
        return cls(
            chrome_driver_path=os.getenv('CHROME_DRIVER_PATH', '/usr/bin/chromedriver'),
            website_url=os.getenv('WEBSITE_URL', 'https://chat.openai.com'),
            wait_timeout=int(os.getenv('WAIT_TIMEOUT', '20')),
            repo_path=os.getenv('REPO_PATH', '.'),
            comparison_output=os.getenv('COMPARISON_OUTPUT', 'changes.json')
        ) 