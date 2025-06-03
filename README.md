# ChatGPT Selenium Scraper

A robust Python script using Selenium to track changes on ChatGPT's interface by performing daily screenshots and HTML captures with automatic comparison.

## Features

- **Advanced Selenium Integration**: Uses both regular Selenium and undetected-chromedriver for reliable access
- **Anti-Detection Measures**: Multiple techniques to bypass bot detection
- **CloudFlare Bypass**: Enhanced waiting strategies to handle protection pages
- **Content Comparison**: Automatic HTML diff generation to detect UI changes
- **GitHub Actions Integration**: Automated daily scraping with customizable schedule
- **Smart Notifications**: Creates GitHub issues when significant changes are detected
- **Optional Authentication**: Support for authenticated scraping with secure credential handling
- **Comprehensive Error Handling**: Robust retry mechanisms and detailed logging

## Prerequisites

- Python 3.10+
- Chrome browser
- ChromeDriver
- Git (configured with push access to your repository)

## Installation

1. Clone the repository: 

```bash
git clone <your-repo-url>
cd chatgpt-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Install ChromeDriver:
   - Download the appropriate version for your Chrome browser from [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/)
   - Place it in a location accessible by your system (e.g., `/usr/bin/chromedriver`)

4. Create and configure the `.env` file:
```env
CHROME_DRIVER_PATH=/usr/bin/chromedriver
WEBSITE_URL=https://chat.openai.com
WAIT_TIMEOUT=60
REPO_PATH=.
COMPARISON_OUTPUT=changes.json

# Optional: Specify custom path to Chrome binary (e.g., /opt/google/chrome/chrome)
# If not set, Selenium will attempt to find it automatically.
# CHROME_BINARY_PATH=/path/to/your/chrome

# Optional authentication
# If OPENAI_USERNAME and OPENAI_PASSWORD are provided, the script will attempt to log in.
# OPENAI_USERNAME=your_username
# OPENAI_PASSWORD=your_password
# USE_COOKIES=true
# COOKIES_PATH=cookies.json
```

## Usage

Run the script:
```bash
python scrape_chatgpt.py
```

The script will:
1. Launch a headless Chrome browser
2. Navigate to the ChatGPT website
3. Handle any CloudFlare protection
4. Attempt to log in if `OPENAI_USERNAME` and `OPENAI_PASSWORD` are set in `.env` or if `USE_COOKIES=true` and a valid `cookies.json` exists.
5. Save the page source to a timestamped file in `scraped_pages/`
6. Compare with the previous scrape to detect changes
7. Generate a changes.json file with diff information
8. Commit and push changes to the git repository

### GitHub Actions Workflow

The included GitHub Actions workflow (`scrape.yml`) provides:

- Automated daily scraping at 2 AM UTC (customizable)
- Manual trigger option
- Automatic push of changes
- Issue creation for significant UI changes

To use with private credentials, set the following GitHub repository secrets:
- `OPENAI_USERNAME`: Your ChatGPT username (if you want the script to log in)
- `OPENAI_PASSWORD`: Your ChatGPT password (if you want the script to log in)
- `CHROME_BINARY_PATH`: (Optional) Custom path to your Chrome binary.

## Project Structure

```
chatgpt-scraper/
├── scrape_chatgpt.py    # Main script with enhanced scraping logic
├── login.py             # Optional authentication module
├── cleanup.py           # Utility to remove old scrapes
├── tests/               # Test suite
│   └── test_scraper.py  # Unit tests
├── .github/workflows/   # GitHub Actions
│   └── scrape.yml       # Workflow definition
├── .env                 # Configuration file
├── .gitignore           # Git ignore rules
├── README.md            # Documentation
├── requirements.txt     # Dependencies
└── scraped_pages/       # Output directory
```

## Advanced Configuration

### Timeouts and Retries

- `WAIT_TIMEOUT`: Selenium wait timeout in seconds (default: 60)
- The scraper includes built-in retry mechanisms for transient failures

### Content Comparison Options

The change detection looks for meaningful differences while ignoring noise like:
- JavaScript changes
- Meta tags
- Styling elements

### Running Tests

```bash
python -m pytest tests/
```

## Troubleshooting

### CloudFlare Challenges

If CloudFlare challenges persist:
1. Increase the `WAIT_TIMEOUT` value
2. Ensure your Chrome and ChromeDriver versions match
3. Try running without headless mode for debugging

### Authentication Issues

If you're having login problems:
1. Verify credentials are correct
2. Delete any existing cookies.json file
3. Run once with `USE_COOKIES=false` to generate fresh cookies

## License

MIT License

## Author

Your Name

---

**Note**: This tool is for educational and research purposes only. Always respect OpenAI's terms of service and rate limits.