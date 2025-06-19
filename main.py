import os
import csv
import pandas as pd
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com"

CSV_FILE_PATH = "Merged_Contact_Scores.csv"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {REALNEX_API_KEY}"
}


@app.route("/upload", methods=["PUT"])
def upload_csv():
    with open(CSV_FILE_PATH, "wb") as f:
        f.write(request.data)
    return "Upload successful", 200


@app.route("/batch_push", methods=["POST"])
def batch_push():
    try:
        with open(CSV_FILE_PATH, "r", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            results = []

            for row in reader:
                if not row or not isinstance(row, dict):
                    continue

                contact_key = row.get("contact_key", "").strip()
                gpt_score = row.get("GPT Score", "").strip()
                last_scored = row.get("Last Scored", "").strip()

                if not contact_key:
                    print(f"Skipping row with missing contact_key: {row}")
                    continue

                url = f"{REALNEX_API_BASE}/api/v1/Crm/contact/{contact_key}"
                payload = {
                    "user_3": gpt_score,
                    "user_4": "Batch Scored",
                    "user_8": last_scored,
                }

                response = requests.put(url, headers=headers, json=payload)
                print(f"Pushed to {contact_key} with status {response.status_code}: {response.text}")

                results.append({
                    "contact_key": contact_key,
                    "status": response.status_code,
                    "body": response.text
                })

        return jsonify(results)

    except Exception as e:
        print(f"Error in batch_push: {e}")
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
