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

# ✅ OPEN BY SHEET NAME
spreadsheet = client.open("RealNex API Test")
worksheet = spreadsheet.worksheet("RealNex API Test")  # tab name
data = pd.DataFrame(worksheet.get_all_records())

# === REALNEX CONFIG ===
REALNEX_BASE_URL = "https://api.realnex.com"

# === SYNC LOOP ===
for i, row in data.iterrows():
    contact_key = row.get("contact_key") or row.get("account_key")
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
        if response.status_code == 200:
            print(f"✅ Updated contact {contact_key} with score {score}")
        else:
            print(f"❌ Error for {contact_key}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Exception for {contact_key}: {str(e)}")

print("🎉 Sync completed!")
