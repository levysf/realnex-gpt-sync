import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask

app = Flask(__name__)

# Set up Google Sheets access
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_CREDS_JSON"]), scopes=scope)
client = gspread.authorize(creds)

# Use environment variable for sheet name
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "RealNex API Test")  # Updated default

try:
    spreadsheet = client.open(GOOGLE_SHEET_NAME)
    worksheet = spreadsheet.sheet1
    print(f"✅ Successfully connected to Google Sheet: {GOOGLE_SHEET_NAME}")
except Exception as e:
    print(f"❌ Failed to open Google Sheet '{GOOGLE_SHEET_NAME}': {e}")
    print("Available sheets:")
    try:
        sheets = client.list()
        for sheet in sheets[:10]:  # Show first 10 sheets
            print(f"  - {sheet.title}")
    except:
        print("  Could not list available sheets")
    raise

# Get RealNex environment variables
REALNEX_API_KEY = os.environ["REALNEX_API_KEY"]
REALNEX_CONTACT_ID = os.environ["REALNEX_CONTACT_ID"]  # Test contact ID

# Remove curly braces if present
REALNEX_CONTACT_ID = REALNEX_CONTACT_ID.strip('{}')

headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {REALNEX_API_KEY}"
}

@app.route("/")
def test_realnex_fields():
    test_payload_fax = {
        "fax": "415-555-0000"
    }
    
    test_payload_user_3 = {
        "user_3": "TESTING USER 3 FIELD"
    }
    
    # Try multiple possible endpoints
    possible_endpoints = [
        f"https://sync.realnex.com/api/v1/contact/{REALNEX_CONTACT_ID}",
        f"https://sync.realnex.com/api/v1/contacts/{REALNEX_CONTACT_ID}",
        f"https://sync.realnex.com/v1/contact/{REALNEX_CONTACT_ID}",
        f"https://sync.realnex.com/v1/contacts/{REALNEX_CONTACT_ID}",
        f"https://sync.realnex.com/api/contact/{REALNEX_CONTACT_ID}",
        f"https://sync.realnex.com/contact/{REALNEX_CONTACT_ID}"
    ]
    
    results = {}
    
    for i, url in enumerate(possible_endpoints):
        endpoint_name = f"endpoint_{i+1}"
        print(f"Testing endpoint {i+1}: {url}")
        
        try:
            # Try fax field
            fax_response = requests.put(url, headers=headers, json=test_payload_fax, timeout=10)
            
            results[endpoint_name] = {
                "url": url,
                "fax_response": {
                    "status_code": fax_response.status_code,
                    "body": fax_response.text[:200] if fax_response.text else "",
                    "success": fax_response.status_code < 400
                }
            }
            
            # If we get a good response, also try user_3
            if fax_response.status_code < 400:
                user3_response = requests.put(url, headers=headers, json=test_payload_user_3, timeout=10)
                results[endpoint_name]["user_3_response"] = {
                    "status_code": user3_response.status_code,
                    "body": user3_response.text[:200] if user3_response.text else "",
                    "success": user3_response.status_code < 400
                }
            
            # Stop testing if we found a working endpoint
            if fax_response.status_code < 400:
                break
                
        except Exception as e:
            results[endpoint_name] = {
                "url": url,
                "error": str(e)
            }
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "tested_endpoints": results
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
