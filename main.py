from flask import Flask, jsonify, request
import os
import csv
import requests
import time
from io import BytesIO
import pandas as pd

app = Flask(__name__)

REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

# Your Google Drive file ID
GOOGLE_DRIVE_FILE_ID = "1vudyvYwyr7R1qYLJY4TBOin5mlbyKi1M"

# Health check endpoint
@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync service is live", 200

# Batch push endpoint (downloads file directly from Google Drive)
@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not REALNEX_API_KEY:
        return jsonify({"error": "REALNEX_API_KEY not set"}), 500

    # Construct Google Drive download URL
    gdrive_url = f"https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}"

    try:
        file_response = requests.get(gdrive_url)
        file_response.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500

    try:
        # Read Excel file into DataFrame
        df = pd.read_excel(BytesIO(file_response.content))
    except Exception as e:
        return jsonify({"error": f"Failed to read Excel file: {str(e)}"}), 500

    results = []
    batch = []

    for _, row in df.iterrows():
        contact_key = row.get("contact_key")
        if not contact_key:
            continue
        payload = {
            "user3": row.get("GPT Score", ""),
            "user4": row.get("Next Action", ""),
            "user8": row.get("Last Scored", "")
        }
        batch.append((contact_key, payload))

    for i, (contact_key, payload) in enumerate(batch):
        url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}"
        headers = {
            "Authorization": f"Bearer {REALNEX_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.put(url, json=payload, headers=headers)
        results.append({
            "contact_key": contact_key,
            "status": response.status_code,
            "body": response.text
        })

        if (i + 1) % 100 == 0:
            time.sleep(1)

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)