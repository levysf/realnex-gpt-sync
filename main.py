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

# === LOAD SHEET ===
spreadsheet = client.open("RealNex API Test")
worksheet = spreadsheet.worksheet("RealNex API Test")
data = pd.DataFrame(worksheet.get_all_records())

# === REALNEX CONFIG ===
REALNEX_BASE_URL = "https://sync.realnex.com/api/investor"
HEADERS = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Content-Type": "application/json"
}

# === SYNC LOOP ===
for i, row in data.iterrows():
    contact_key = row.get("contact_key") or row.get("account_key")
    score = row.get("GPT Score")

    if not contact_key or pd.isna(score):
        continue

    url = f"{REALNEX_BASE_URL}/{contact_key}"
    payload_fax = {"fax": str(score)}
    payload_user3 = {"user_3": str(score)}

    try:
        response = requests.put(url, headers=HEADERS, json=payload_fax)
        if response.status_code == 200:
            print(f"✅ Updated {contact_key} in fax field: {score}")
        else:
            print(f"⚠️ Fax update failed ({response.status_code}), retrying with user_3...")
            response2 = requests.put(url, headers=HEADERS, json=payload_user3)
            if response2.status_code == 200:
                print(f"✅ Updated {contact_key} in user_3 field: {score}")
            else:
                print(f"❌ Failed user_3 too — {response2.status_code}: {response2.text}")
    except Exception as e:
        print(f"❌ Exception for {contact_key}: {str(e)}")

print("🚀 Fallback sync complete.")
