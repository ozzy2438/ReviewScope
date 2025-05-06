"""
Utility functions for the Amazon Scraper & Analyzer application.
"""
import os
import re
import json
import pandas as pd
from datetime import datetime

def ensure_directory_exists(directory_path):
    """Ensure that a directory exists, create it if it doesn't"""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def clean_filename(filename):
    """Clean a string to be used as a filename"""
    # Replace spaces and special characters with underscores
    return re.sub(r'[^\w\-\.]', '_', filename)

def format_timestamp():
    """Return formatted timestamp for filenames"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def load_json_file(file_path):
    """Load JSON data from a file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {str(e)}")
        return None

def save_json_file(data, file_path):
    """Save data as JSON to a file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {str(e)}")
        return False
