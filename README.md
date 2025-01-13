# ChatGPT Selenium Scraper

A robust Python script using Selenium to scrape ChatGPT pages and automatically commit changes to a git repository.

## Features

- Automated web scraping using Selenium and Chrome in headless mode
- Automatic git commit and push functionality
- Configurable through environment variables
- Comprehensive error handling and logging
- Retry mechanism for network operations
- Beautiful Soup integration for HTML parsing

## Prerequisites

- Python 3.7+
- Chrome browser
- ChromeDriver
- Git (configured with push access to your repository)

## Installation

1. Clone the repository: 

bash
git clone <your-repo-url>
cd Selenium-Test

2. Install required packages:
```bash
pip install selenium beautifulsoup4 python-dotenv
```

3. Install ChromeDriver:
   - Download the appropriate version for your Chrome browser from [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/)
   - Place it in a location accessible by your system (e.g., `/usr/bin/chromedriver`)

4. Create and configure the `.env` file:
```env
CHROME_DRIVER_PATH=/usr/bin/chromedriver
WEBSITE_URL=https://chat.openai.com
WAIT_TIMEOUT=20
REPO_PATH=.
```

## Usage

Run the script:
```bash
python scrape_chatgpt.py
```

The script will:
1. Launch a headless Chrome browser
2. Navigate to the specified URL
3. Save the page source to a timestamped file in `scraped_pages/`
4. Commit and push changes to the git repository

## Configuration

Modify the `.env` file to customize:
- `CHROME_DRIVER_PATH`: Path to ChromeDriver executable
- `WEBSITE_URL`: Target URL to scrape
- `WAIT_TIMEOUT`: Maximum wait time for page elements (seconds)
- `REPO_PATH`: Path to git repository

## Logging

Logs are written to:
- Console output
- `scraper.log` file

## Error Handling

The script includes:
- Retry mechanism for network operations
- Specific exception handling for Selenium
- Git operation error handling
- Comprehensive logging

## Project Structure

```
Selenium-Test/
├── scrape_chatgpt.py    # Main script
├── .env                 # Configuration file
├── README.md           # This file
├── scraper.log         # Log file
└── scraped_pages/      # Output directory
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]

## Author

[Your name]

