import os
import json
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ENV
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]
GOOGLE_SHEET_NAME = os.environ["GOOGLE_SHEET_NAME"]
REALNEX_API_KEY = os.environ["REALNEX_API_KEY"]

# Auth: Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDS_JSON), scope)
client = gspread.authorize(creds)
spreadsheet = client.open(GOOGLE_SHEET_NAME)
sheet = spreadsheet.sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

# TEST VALUE TO PUSH
TEST_CONTACT_KEY = df.iloc[0]["contact_key"]
TEST_VALUE = f"PUT_TEST_{os.environ.get('RENDER_GIT_COMMIT', 'manual')}"

# PUT to Fax Field
put_url = f"https://sync.realnex.com/api/v1/contact/{TEST_CONTACT_KEY}"
headers = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "fax": TEST_VALUE
}

res = requests.put(put_url, headers=headers, data=json.dumps(payload))

print("=== PUT RESPONSE ===")
print("Status Code:", res.status_code)
print("Response Body:", res.text)

# Optional fallback test to user_3 if fax fails
if res.status_code >= 400:
    fallback_payload = {
        "user_3": TEST_VALUE
    }
    res2 = requests.put(put_url, headers=headers, data=json.dumps(fallback_payload))
    print("=== FALLBACK TO user_3 ===")
    print("Status Code:", res2.status_code)
    print("Response Body:", res2.text)
