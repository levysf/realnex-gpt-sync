import os
import requests
import pandas as pd
from io import StringIO
from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables
REALNEX_API_TOKEN = os.getenv('REALNEX_API_KEY')
REALNEX_SELECTED_DB = os.getenv('REALNEX_SELECTED_DB')
GOOGLE_DRIVE_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID') or "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"
REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

def download_csv(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))

def build_payload(user3_value: str) -> dict:
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
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    payload = build_payload(user3_value)
    return requests.put(url, json=payload, headers=headers)

def run_sync() -> dict:
    if not REALNEX_API_TOKEN or not REALNEX_SELECTED_DB:
        return {"error": "Missing REALNEX_API_TOKEN or REALNEX_SELECTED_DB"}

    try:
        df = download_csv(GOOGLE_DRIVE_FILE_ID)
    except Exception as e:
        return {"error": f"CSV download failed: {str(e)}"}

    if "contact_key" not in df.columns or "GPT Score" not in df.columns:
        return {"error": "CSV must contain 'contact_key' and 'GPT Score'"}

    results = []
    for _, row in df.iterrows():
        contact_key = str(row["contact_key"]).strip()
        score = row["GPT Score"]
        if contact_key and pd.notna(score):
            resp = update_contact(contact_key, str(score))
            status = {
                "contact": contact_key,
                "score": score,
                "status": resp.status_code,
                "ok": resp.status_code < 400
            }
            logger.info(status)
            results.append(status)

    return {"updated": results}

# Flask route for Render health and manual trigger
@app.route("/run", methods=["GET"])
def trigger_run():
    result = run_sync()
    return jsonify(result)

@app.route("/", methods=["GET"])
def home():
    return "RealNex Sync Service is up and running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
