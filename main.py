import os
import requests
import pandas as pd
from io import StringIO
from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Render (needs a web server)
app = Flask(__name__)

# Environment variables
REALNEX_API_TOKEN = os.getenv('REALNEX_API_KEY')
REALNEX_SELECTED_DB = os.getenv('REALNEX_SELECTED_DB') 
GOOGLE_DRIVE_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID')

REALNEX_API_BASE = "https://sync.realnex.com/api/v1"
DEFAULT_FILE_ID = "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"

def download_csv(file_id: str) -> pd.DataFrame:
    """Download CSV from Google Drive"""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception as e:
        logger.error(f"Failed to download CSV: {e}")
        raise

def build_payload(user3_value: str) -> dict:
    """Build the payload for RealNex API"""
    return {
        "broker": False,
        "rehabs": False,
        "jointVenture": False,
        "tripleNet": False,
        "singleTenant": False,
        "multipleTenant": False,
        "singleFamily": False,
        "creditTenant": False,
        "userFields": {
            "user3": user3_value
        },
        "logicalFields": {f"logical{i}": False for i in range(1, 25)}
    }

def update_contact(contact_key: str, user3_value: str) -> requests.Response:
    """Update contact in RealNex with multiple retry strategies"""
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    
    # Try different
