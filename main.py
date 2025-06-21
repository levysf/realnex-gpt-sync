import os
import requests
import gspread
from google.oauth2.service_account import Credentials

# Load credentials from environment variables
REALNEX_API_KEY = os.environ["REALNEX_API_KEY"]
GOOGLE_DRIVE_FILE_ID = os.environ["GOOGLE_DRIVE_FILE_ID"]
GOOGLE_SHEET_NAME = os.environ["GOOGLE_SHEET_NAME"]
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]

# Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(eval(GOOGLE_CREDS_JSON), scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet and worksheet
spreadsheet = client.open_by_key(GOOGLE_DRIVE_FILE_ID)
worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)

# Read all data
data = worksheet.get_all_records()

# RealNex API setup
headers = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Content-Type": "application/json"
}
url_template = "https://sync.realnex.com/v1/contacts/{}"

# Loop through rows and update RealNex contacts
for row in data:
    contact_key = row.get("contact_key")
    gpt_score = row.get("GPT Score")
    if not contact_key or gpt_score is None:
        print(f"Skipping row: {row}")
        continue

    # Prepare payload (updating the `fax` field)
    payload = {
        "fax": str(gpt_score)
    }

    url = url_template.format(contact_key)
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"✅ Updated contact {contact_key} with score {gpt_score}")
    else:
        print(f"❌ Failed to update contact {contact_key}: {response.status_code}")
        print("Response:", response.text)
