import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# === ENV VARS ===
REALNEX_API_KEY = os.environ["REALNEX_API_KEY"]
GOOGLE_SERVICE_ACCOUNT_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"]

# === GOOGLE SHEETS AUTH ===
service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_KEY)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
client = gspread.authorize(credentials)

# === SHEET LOAD ===
spreadsheet = client.open("RealNex API Test")
worksheet = spreadsheet.worksheet("RealNex API Test")
rows = worksheet.get_all_records()

# === REALNEX v1 SYNC ===
REALNEX_BASE_URL = "https://sync.realnex.com/api/investor"
headers = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Content-Type": "application/json"
}

for row in rows:
    contact_key = row.get("contact_key")
    score = row.get("GPT Score")

    if not contact_key or score in [None, ""]:
        continue

    url = f"{REALNEX_BASE_URL}/{contact_key}"
    payload = {
        "fax": str(score)
    }

    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ Updated {contact_key} with GPT Score: {score}")
        else:
            print(f"❌ Failed for {contact_key} — {response.status_code}: {response.text}")
    except Exception as e:
        print(f"⚠️ Error updating {contact_key}: {e}")

print("🎉 All done syncing to RealNex!")
