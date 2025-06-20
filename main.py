import os
import requests
import pandas as pd
from io import StringIO
from flask import Flask, jsonify
import logging

# --------------------------
# Logging Configuration
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# Flask App
# --------------------------
app = Flask(__name__)

# --------------------------
# Environment Variables
# --------------------------
REALNEX_API_TOKEN = os.getenv('REALNEX_API_KEY')
GOOGLE_DRIVE_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID', '1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk')  # Default if not set
REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

# --------------------------
# Download CSV from Google Drive
# --------------------------
def download_csv(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        logger.info(f"Downloading CSV from Google Drive file ID: {file_id}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        logger.info(f"CSV download and parse successful. Rows: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Failed to download or parse CSV: {e}")
        raise

# --------------------------
# Build JSON Payload for RealNex
# --------------------------
def build_payload(user3_value: str) -> dict:
    return {
        "userFields": {
            "user3": user3_value
        }
    }

# --------------------------
# Update Single Contact
# --------------------------
def update_contact(contact_key: str, user3_value: str) -> requests.Response:
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = build_payload(user3_value)
    response = requests.put(url, headers=headers, json=payload)
    return response

# --------------------------
# Endpoint to trigger update
# --------------------------
@app.route("/run", methods=["GET"])
def run_update():
    try:
        df = download_csv(GOOGLE_DRIVE_FILE_ID)
        if 'contact_key' not in df.columns or 'GPT Score' not in df.columns:
            return jsonify({"error": "CSV must have 'contact_key' and 'GPT Score' columns"}), 400

        failures = []
        updated = 0

        for _, row in df.iterrows():
            contact_key = row['contact_key']
            gpt_score = str(row['GPT Score'])

            res = update_contact(contact_key, gpt_score)

            if res.status_code == 200:
                updated += 1
            else:
                failures.append({
                    "contact": contact_key,
                    "status": res.status_code,
                    "message": res.text
                })

        return jsonify({"updated": updated, "failures": failures})
    except Exception as e:
        logger.exception("Run failed")
        return jsonify({"error": str(e)}), 500

# --------------------------
# Root
# --------------------------
@app.route("/", methods=["GET"])
def health_check():
    return "RealNex sync service is running!", 200

# --------------------------
# Entry point
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
