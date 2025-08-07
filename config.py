from dataclasses import dataclass
from typing import Optional
import os
import random
from dotenv import load_dotenv
from fake_useragent import UserAgent
from distutils.util import strtobool

# Load environment variables from a .env file before accessing them
load_dotenv()

# ----------------------- runtime switches ----------------------------------
HEADLESS = bool(strtobool(os.getenv("HEADLESS", "1")))  # accepts 0/1 yes/no true/false

# ----------------------- UA / viewport pools -------------------------------
UA_FALLBACK = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/117.0 Safari/537.36",
]
try:
    USER_AGENT = UserAgent().random
except Exception:
    USER_AGENT = random.choice(UA_FALLBACK)

VIEWPORTS = [
    (1920, 1080),
    (1366, 768),
    (1280, 800),
    (1600, 900),
]
VIEWPORT = random.choice(VIEWPORTS)

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
        return cls(
            chrome_driver_path=os.getenv('CHROME_DRIVER_PATH'),
            website_url=os.getenv('WEBSITE_URL', 'https://chat.openai.com'),
            wait_timeout=int(os.getenv('WAIT_TIMEOUT', '20')),
            repo_path=os.getenv('REPO_PATH', '.'),
            comparison_output=os.getenv('COMPARISON_OUTPUT', 'changes.json'),
            chrome_binary_path=os.getenv('CHROME_BINARY_PATH', None)
        )

OPENAI_USERNAME = os.getenv("OPENAI_USERNAME")
OPENAI_PASSWORD = os.getenv("OPENAI_PASSWORD")
