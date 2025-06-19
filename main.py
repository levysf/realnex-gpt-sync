import pandas as pd
import requests
from flask import Flask, request
import os
import sys

app = Flask(__name__)

REALNEX_API_BASE = "https://api.realnex.com"
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {REALNEX_API_KEY}"
}

@app.route('/')
def index():
    return "RealNex GPT Sync is live!"

@app.route('/upload', methods=['PUT'])
def upload():
    with open("Merged_Contact_Scores.csv", "wb") as f:
        f.write(request.get_data())
    print("✅ File uploaded: Merged_Contact_Scores.csv")
    sys.stdout.flush()
    return "Upload successful", 200

@app.route('/batch_push', methods=['POST'])
def batch_push():
    print("🚀 Starting batch push")
    sys.stdout.flush()

    try:
        df = pd.read_csv("Merged_Contact_Scores.csv")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.stdout.flush()
        return "Failed to read CSV", 500

    for index, row in df.iterrows():
        contact_key = row.get("contact_key")
        gpt_score = row.get("GPT Score")
        last_scored = row.get("Last Scored")

        if not contact_key or pd.isna(gpt_score):
            print(f"⚠️ Skipping row {index}: missing data")
            continue

        payload = {
            "user3": str(gpt_score),
            "user4": "Push OK",
            "user8": last_scored
        }

        try:
            url = f"{REALNEX_API_BASE}/api/v1/Crm/contact/{contact_key}"
            response = requests.put(url, json=payload, headers=HEADERS)

            print(f"➡️ {contact_key}: {response.status_code} - {response.text}")
            sys.stdout.flush()

        except Exception as e:
            print(f"❌ Error pushing contact {contact_key}: {e}")
            sys.stdout.flush()

    print("✅ Batch push complete")
    sys.stdout.flush()
    return "Batch push completed", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
