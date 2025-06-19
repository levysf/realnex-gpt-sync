from flask import Flask, request, jsonify
import os
import csv
import requests
import time

app = Flask(__name__)

UPLOAD_FILE = "uploaded.csv"
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

if not REALNEX_API_KEY:
    raise RuntimeError("REALNEX_API_KEY environment variable is required")

@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync service is live", 200

@app.route("/upload", methods=["PUT"])
def upload_file():
    try:
        with open(UPLOAD_FILE, "wb") as f:
            f.write(request.data)
        return "Upload successful", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(UPLOAD_FILE):
        return jsonify({"error": f"CSV file not found at {UPLOAD_FILE}"}), 400

    results = []

    with open(UPLOAD_FILE, newline="", encoding="utf-8") as csvfile:
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

            if (i + 1) % 100 == 0:
                time.sleep(1)

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
