# settings.py
import os
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

REALNEX_API_TOKEN = os.getenv('REALNEX_API_TOKEN') or os.getenv('REALNEX_API_KEY')
REALNEX_SELECTED_DB = os.getenv('REALNEX_SELECTED_DB')
GOOGLE_DRIVE_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID')  # Optional override
