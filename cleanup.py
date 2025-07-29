import os
from datetime import datetime, timedelta
import logging

def cleanup_old_files(directory: str, days: int = 30) -> None:
    """Remove files older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)
                    logging.info(f"Removed old file: {filepath}")
    except Exception:
        logging.exception("Error during cleanup")

if __name__ == "__main__":
    cleanup_old_files("scraped_pages") 