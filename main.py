import os
import requests
import datetime
import pandas as pd
from flask import Flask, jsonify
import logging
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_SELECTED_DB = os.getenv("REALNEX_SELECTED_DB")
REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

GOOGLE_SHEET_ID = "1L7w5XBv8FxG1qgr5ngbpph2sOeDUIRjjPjFqMQbV6vg"
SHEET_RANGE = "RealNex API Test!A:B"  # contact_key in col A, GPT Score in col B

# Path to your Google service account JSON file
SERVICE_ACCOUNT_FILE = "gcp_service_account.json"  # You will upload this to Render
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def fetch_sheet_data():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=SHEET_RANGE).execute()
        values = result.get("values", [])

        if not values:
            raise ValueError("No data found in sheet.")

        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"Google Sheets API error: {e}")
        raise

def build_payload(contact_key: str, score_value: str) -> dict:
    return {
        "contactKey": contact_key,
        "fax": score_value  # Temporarily writing GPT Score to the Fax field
    }

def update_contact(contact_key: str, score_value: str) -> requests.Response:
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    payload = build_payload(contact_key, score_value)
    logger.info(f"Updating contact {contact_key} with GPT Score {score_value}...")
    return requests.put(url, json=payload, headers=headers)

@app.route("/run")
def run_update():
    if not REALNEX_API_KEY or not REALNEX_SELECTED_DB:
        return jsonify({"error": "Missing REALNEX_API_KEY or REALNEX_SELECTED_DB"}), 400

    try:
        df = fetch_sheet_data()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if "contact_key" not in df.columns or "GPT Score" not in df.columns:
        return jsonify({"error": "Sheet must contain 'contact_key' and 'GPT Score' columns"}), 400

    total = 0
    failures = []

    for _, row in df.iterrows():
        contact_key = str(row["contact_key"]).strip()
        score = row["GPT Score"]
        if contact_key and pd.notna(score):
            resp = update_contact(contact_key, str(score))
            if resp.status_code >= 400:
                failures.append({"contact": contact_key, "status": resp.status_code, "message": resp.text})
            else:
                total += 1

    return jsonify({"updated": total, "failures": failures})

@app.route("/")
def home():
    return "✅ Server is running. Visit /run to trigger updates from Google Sheets."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)