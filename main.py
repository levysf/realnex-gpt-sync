from flask import Flask, jsonify, request
import os
import csv
import requests
import time

app = Flask(__name__)

# Path to your local file
CSV_FILE_PATH = r"C:\Users\joe\Downloads\RealNex API Test.csv"

# RealNex API config
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

# Validate API key early
if not REALNEX_API_KEY:
    raise RuntimeError("REALNEX_API_KEY environment variable is required")

@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync service is live", 200

# Upload is disabled in this version
@app.route("/upload", methods=["PUT"])
def upload_file():
    return "Upload endpoint is disabled in this version. File path is hardcoded.", 400

@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(CSV_FILE_PATH):
        return jsonify({"error": f"File not found: {CSV_FILE_PATH}"}), 400

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
                result = {
                    "contact_key": contact_key,
                    "status": response.status_code,
                    "body": response.text
                }

                # If rate-limited, sleep and retry
                if response.status_code == 429:
                    time.sleep(5)
                    response = requests.put(url, json=payload, headers=headers)
                    result["retry_status"] = response.status_code
                    result["retry_body"] = response.text

                results.append(result)
            except Exception as e:
                results.append({
                    "contact_key": contact_key,
                    "error": str(e)
                })

            # Throttle every 100 requests
            if (i + 1) % 100 == 0:
                time.sleep(1)

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
