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
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
client = gspread.authorize(credentials)

# Open spreadsheet and worksheet
spreadsheet = client.open("RealNex API Test")
worksheet = spreadsheet.worksheet("RealNex API Test")
data = pd.DataFrame(worksheet.get_all_records())

# === REALNEX CONFIG ===
REALNEX_BASE_URL = "https://api.realnex.com"

# === SYNC LOOP ===
for i, row in data.iterrows():
    contact_key = row.get("contact_key")
    score = row.get("GPT Score")

    if not contact_key or pd.isna(score):
        continue

    url = f"{REALNEX_BASE_URL}/v2/contacts/{contact_key}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": REALNEX_API_KEY
    }
    payload = {
        "fax": str(score)  # Writing GPT Score into the fax field
    }

    try:
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        print(f"\n➡️ PUT {url}")
        print(f"📦 Payload: {payload}")
        print(f"📬 Status: {response.status_code}")
        print(f"📨 Response: {response.text}")
    except Exception as e:
        print(f"⚠️ Exception for {contact_key}: {str(e)}")

print("\n🎉 Sync completed!")
