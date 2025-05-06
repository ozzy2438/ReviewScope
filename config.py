import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask configuration
SECRET_KEY = 'your-secret-key-here'  # Change this to a random string
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = timedelta(days=1)

# Folders for data storage
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
RAW_DATA_FOLDER = os.path.join(DATA_FOLDER, 'raw')
PROCESSED_DATA_FOLDER = os.path.join(DATA_FOLDER, 'processed')

# Make sure directories exist
for folder in [DATA_FOLDER, RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Selenium configuration
HEADLESS_BROWSER = True  # Run browser in headless mode
PAGE_LOAD_TIMEOUT = 30  # Seconds