import os
import requests
import datetime
import pandas as pd
from flask import Flask, jsonify
from io import StringIO
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_SELECTED_DB = os.getenv("REALNEX_SELECTED_DB")
GOOGLE_DRIVE_FILE_ID = os.getenv("GOOGLE_DRIVE_FILE_ID") or "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"
REALNEX_ODATA_BASE = "https://sync.realnex.com/api/v1/CrmOData"
REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

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

# Build RealNex payload for OContacts endpoint
def build_payload(contact_key: str, user3_value: str) -> dict:
    return {
        "contactKey": contact_key,
        "investorInfo": {
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
    }

# Update a contact using POST to OContacts
def update_contact(contact_key: str, user3_value: str) -> requests.Response:
    url = f"{REALNEX_API_BASE}/Crm/OContacts"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    payload = build_payload(contact_key, user3_value)
    logger.info(f"Posting score {user3_value} to contact {contact_key}...")
    logger.debug(f"Payload: {json.dumps(payload)}")
    return requests.post(url, json=payload, headers=headers)

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

@app.route("/test-one")
def test_single_contact():
    if not REALNEX_API_KEY or not REALNEX_SELECTED_DB:
        return jsonify({"error": "Missing REALNEX_API_KEY or REALNEX_SELECTED_DB"}), 400

    # Replace with one of your known valid contact keys
    contact_key = "8E042807-1C2F-449A-83C7-B46512424444"
    test_score = "88"

    response = update_contact(contact_key, test_score)
    return jsonify({
        "contact": contact_key,
        "score": test_score,
        "status": response.status_code,
        "message": response.text[:300]  # limit to avoid huge logs
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)