import os
import requests
import datetime
import pandas as pd
from flask import Flask, jsonify
from io import StringIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_SELECTED_DB = os.getenv("REALNEX_SELECTED_DB")
GOOGLE_DRIVE_FILE_ID = os.getenv("GOOGLE_DRIVE_FILE_ID") or "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"
REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

# Use OData API for reading
REALNEX_ODATA_BASE = "https://sync.realnex.com/api/v1/CrmOData"

# Download from Google Drive
def download_csv(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception as e:
        logger.error(f"Failed to download CSV: {e}")
        raise

# Build RealNex payload
def build_payload(user3_value: str) -> dict:
    return {
        "userFields": {
            "user3": user3_value
        }
    }

# Update a contact using PUT
def update_contact(contact_key: str, user3_value: str) -> requests.Response:
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    payload = build_payload(user3_value)
    logger.info(f"Updating {contact_key} with score {user3_value}...")
    return requests.put(url, json=payload, headers=headers)

# Read contacts from OData (used in testing)
def get_contacts():
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    res = requests.get(f"{REALNEX_ODATA_BASE}/Contacts", headers=headers, params={"$top": 10})
    logger.info(f"Contact API status: {res.status_code}")
    return res.json().get("value", []) if res.status_code == 200 else []

@app.route("/run")
def run_update():
    if not REALNEX_API_KEY or not REALNEX_SELECTED_DB:
        return jsonify({"error": "Missing REALNEX_API_KEY or REALNEX_SELECTED_DB"}), 400

    try:
        df = download_csv(GOOGLE_DRIVE_FILE_ID)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if "contact_key" not in df.columns or "GPT Score" not in df.columns:
        return jsonify({"error": "CSV must contain 'contact_key' and 'GPT Score' columns"}), 400

    total = 0
    failures = []

    for _, row in df.iterrows():
        contact_key = str(row["contact_key"]).strip()
        score = row["GPT Score"]
        if contact_key and pd.notna(score):
            resp = update_contact(contact_key, str(score))
            if resp.status_code >= 400:
                failures.append({"contact": contact_key, "status": resp.status_code, "message": resp.text})
            else:
                total += 1

    return jsonify({"updated": total, "failures": failures})

@app.route("/")
def home():
    return "✅ Server is running. Visit /run to trigger updates."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
