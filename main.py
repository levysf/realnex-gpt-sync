import os
import json
import pandas as pd
import gspread
import requests
from google.oauth2.service_account import Credentials

# === LOAD SECRETS FROM ENV ===
GOOGLE_SERVICE_ACCOUNT_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"]
REALNEX_API_KEY = os.environ["REALNEX_API_KEY"]

# === AUTH GOOGLE SHEETS ===
service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_KEY)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
client = gspread.authorize(credentials)

# === READ SHEET ===
spreadsheet = client.open("RealNex API Test")
worksheet = spreadsheet.worksheet("RealNex API Test")  # Exact tab name
data = pd.DataFrame(worksheet.get_all_records())

# === SYNC LOOP ===
REALNEX_BASE_URL = "https://api.realnex.com"
headers = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Content-Type": "application/json"
}

for i, row in data.iterrows():
    contact_key = row.get("contact_key")
    score = row.get("GPT Score")

    if not contact_key or pd.isna(score):
        continue

    url = f"{REALNEX_BASE_URL}/api/investor/{contact_key}"
    payload = {
        "fax": str(score)
    }

    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ Updated contact {contact_key} with GPT Score {score}")
        else:
            print(f"❌ Failed for {contact_key} - {response.status_code}: {response.text}")
    except Exception as e:
        print(f"⚠️ Exception for {contact_key}: {str(e)}")

print("🎉 All GPT Scores synced to RealNex fax field.")
