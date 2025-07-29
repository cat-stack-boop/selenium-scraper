from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class Config:
    chrome_driver_path: Optional[str]
    website_url: str
    wait_timeout: int
    repo_path: str
    comparison_output: str
    chrome_binary_path: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'Config':
        load_dotenv()
        return cls(
            chrome_driver_path=os.getenv('CHROME_DRIVER_PATH'),
            website_url=os.getenv('WEBSITE_URL', 'https://chat.openai.com'),
            wait_timeout=int(os.getenv('WAIT_TIMEOUT', '20')),
            repo_path=os.getenv('REPO_PATH', '.'),
            comparison_output=os.getenv('COMPARISON_OUTPUT', 'changes.json'),
            chrome_binary_path=os.getenv('CHROME_BINARY_PATH', None)
        ) 
