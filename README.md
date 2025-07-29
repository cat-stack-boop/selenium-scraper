# ChatGPT Selenium Scraper

### Quick\u00a0start\u00a0(headless)

```bash
docker build -t chatgpt-scraper .
docker run --rm \
  -e OPENAI_USERNAME=you@example.com \
  -e OPENAI_PASSWORD='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022' \
  chatgpt-scraper
```

### Debug mode (GUI)

```bash
HEADLESS=false python -m scrape_chatgpt
```

### CI matrix

CI now runs the scraper nightly across **stable**, **beta** and **dev** Chrome channels to catch driver drift early.

# JSON logs

All runtime output is machine\u2011parseable JSON; pipe it into Datadog, GCP\u00a0Cloud\u00a0Logging or `jq` locally:

```bash
python -m scrape_chatgpt | jq .
```
