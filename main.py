from flask import Flask, request, jsonify
import os
import csv
import requests
import time

app = Flask(__name__)

REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"
CSV_FILE_PATH = r"C:\Users\joe\Downloads\RealNex API Test.csv"  # updated path

# Check API key at startup
if not REALNEX_API_KEY:
    raise RuntimeError("REALNEX_API_KEY environment variable is required")

# Health check
@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync service is live", 200

# Upload endpoint (unused if reading from fixed path)
@app.route("/upload", methods=["PUT"])
def upload_file():
    return "Upload endpoint is disabled in this version. File path is hardcoded.", 400

# Batch push endpoint
@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(CSV_FILE_PATH):
        return jsonify({"error": f"CSV file not found at {CSV_FILE_PATH}"}), 400

    results = []
    with open(CSV_FILE_PATH, newline="", encoding="utf-8") as csvfile:
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

            try:
                response = requests.put(url, json=payload, headers=headers)
                results.append({
                    "contact_key": contact_key,
                    "status": response.status_code,
                    "body": response.text
                })

                if response.status_code == 429:
                    time.sleep(5)
                elif (i + 1) % 100 == 0:
                    time.sleep(1)

            except Exception as e:
                results.append({
                    "contact_key": contact_key,
                    "status": "error",
                    "error": str(e)
                })

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
