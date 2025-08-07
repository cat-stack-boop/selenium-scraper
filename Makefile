.PHONY: install run clean test

install:
	pip3 install -r requirements.txt

run:
	python3 scrape_chatgpt.py

clean:
	python3 cleanup.py
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

test:
	python3 -m pytest tests/ 
