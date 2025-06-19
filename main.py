from flask import Flask, jsonify
import os
import csv
import requests
import time

app = Flask(__name__)

CSV_FILE_PATH = "RealNex API Test.csv"
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

# Fail fast if API key is not set
if not REALNEX_API_KEY:
    raise RuntimeError("REALNEX_API_KEY environment variable is required")

@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync service is live", 200

@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(CSV_FILE_PATH):
        return jsonify({"error": f"CSV file not found at {CSV_FILE_PATH}"}), 400

    results = []
    with open(CSV_FILE_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        batch = []
        for row in reader:
            contact_key = row.get("contact_key", "").strip()
            if not contact_key:
                continue
            payload = {
                "user3": row.get("GPT Score", "").strip(),
                "user4": row.get("Next Action", "").strip(),
                "user8": row.get("Last Scored", "").strip(),
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
