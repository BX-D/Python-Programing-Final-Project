import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate a filename with the current date
log_filename = f"logs/nba_api_{datetime.now().strftime('%Y-%m-%d')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)