from flask import Flask, request, jsonify
import os
import csv
import requests
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = "uploaded.csv"
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

if not REALNEX_API_KEY:
    raise RuntimeError("REALNEX_API_KEY environment variable is required")

# Health check endpoint
@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync service is live", 200

# Upload endpoint
@app.route("/upload", methods=["PUT"])
def upload_file():
    if not REALNEX_API_KEY:
        return jsonify({"error": "REALNEX_API_KEY not set"}), 500

    with open(UPLOAD_FOLDER, "wb") as f:
        f.write(request.data)
    return "Upload successful", 200

# Batch push endpoint
@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not REALNEX_API_KEY:
        return jsonify({"error": "REALNEX_API_KEY not set"}), 500

    if not os.path.exists(UPLOAD_FOLDER):
        return jsonify({"error": "No uploaded file found"}), 400

    results = []
    with open(UPLOAD_FOLDER, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        batch = []
        for row in reader:
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

            # throttle after every 100 requests to respect API limits
            if (i + 1) % 100 == 0:
                time.sleep(1)

            if response.status_code == 429:
                time.sleep(60)

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
