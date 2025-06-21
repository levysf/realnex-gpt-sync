import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials

# ------------------------------
# STEP 1 – Load data from Google Sheet
# ------------------------------

# Load Google service account credentials from env
service_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"])
creds = Credentials.from_service_account_info(
    service_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)

# Open Google Sheet and read data from the correct tab
spreadsheet = client.open("RealNex API Test")
sheet = spreadsheet.worksheet("RealNex API Test")  # Tab name must match

# Read rows into dictionaries
rows = sheet.get_all_records()

# Parse score updates
score_updates = [
    {"contact_key": row["contact_key"], "score": row["GPT Score"]}
    for row in rows if row.get("contact_key") and row.get("GPT Score") is not None
]

# ------------------------------
# STEP 2 – Push scores to RealNex
# ------------------------------

REALNEX_API_TOKEN = os.environ["REALNEX_API_KEY"]
headers = {
    "Authorization": f"Bearer {REALNEX_API_TOKEN}",
    "Content-Type": "application/json"
}

for entry in score_updates:
    payload = {
        "fax": str(entry["score"])
    }
    url = f"https://api.realnex.com/api/investor/{entry['contact_key']}"
    
    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ Updated {entry['contact_key']} with GPT Score: {entry['score']}")
        else:
            print(f"❌ {response.status_code} for {entry['contact_key']}: {response.text}")
    except Exception as e:
        print(f"❌ Exception for {entry['contact_key']}: {e}")
