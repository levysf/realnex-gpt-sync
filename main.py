import os
import csv
import requests
from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Increase allowed upload size to 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

REALNEX_API_KEY = os.environ.get("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

UPLOAD_PATH = "latest_uploaded.csv"


@app.route("/upload", methods=["PUT"])
def upload():
    with open(UPLOAD_PATH, "wb") as f:
        f.write(request.data)
    return "Upload successful", 200


@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(UPLOAD_PATH):
        return "No uploaded file found.", 400

    results = []

    with open(UPLOAD_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contact_key = row.get("contact_key")
            gpt_score = row.get("GPT Score", "")
            last_scored = row.get("Last Scored", "")
            if not contact_key:
                continue

            payload = {
                "user_3": gpt_score,
                "user_8": last_scored
            }

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
            except Exception as e:
                results.append({
                    "contact_key": contact_key,
                    "status": "error",
                    "body": str(e)
                })

    return jsonify(results)


@app.route("/", methods=["GET"])
def index():
    return "RealNex GPT Sync is live!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
