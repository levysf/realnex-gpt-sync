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
    # Test both regular and /full endpoints with correct structure
    regular_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}"
    full_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}/full"
    
    # Also test with URL-encoded curly braces (like in the curl example)
    contact_id_encoded = f"%7B{REALNEX_CONTACT_ID}%7D"
    full_endpoint_encoded = f"https://sync.realnex.com/api/v1/Crm/contact/{contact_id_encoded}/full"
    
    results = {}
    
    # First, get the full contact data
    try:
        full_response = requests.get(full_endpoint, headers=headers, timeout=10)
        results["GET_full_contact"] = {
            "status": full_response.status_code,
            "success": full_response.status_code < 400,
            "endpoint": full_endpoint,
            "body_preview": full_response.text[:800] if full_response.text else ""
        }
        
        if full_response.status_code < 400:
            full_contact_data = full_response.json()
            
            # Test 1: Update fax field (root level)
            full_contact_data["fax"] = "415-555-FAX-TEST"
            
            fax_update_response = requests.put(regular_endpoint, headers=headers, json=full_contact_data, timeout=10)
            results["PUT_fax_update"] = {
                "status": fax_update_response.status_code,
                "success": fax_update_response.status_code < 400,
                "body_preview": fax_update_response.text[:500] if fax_update_response.text else "",
                "approach": "Updated fax field at root level"
            }
            
            # Test 2: Update user3 in the correct nested location
            if "investorData" in full_contact_data and "userFields" in full_contact_data["investorData"]:
                full_contact_data_copy = full_response.json()  # Fresh copy
                full_contact_data_copy["investorData"]["userFields"]["user3"] = "GPT-SCORE-SUCCESS"
                
                user3_update_response = requests.put(regular_endpoint, headers=headers, json=full_contact_data_copy, timeout=10)
                results["PUT_user3_nested"] = {
                    "status": user3_update_response.status_code,
                    "success": user3_update_response.status_code < 400,
                    "body_preview": user3_update_response.text[:500] if user3_update_response.text else "",
                    "approach": "Updated investorData.userFields.user3",
                    "current_user3_value": full_contact_data.get("investorData", {}).get("userFields", {}).get("user3")
                }
            
            # Test 3: Try with URL-encoded endpoint
            encoded_response = requests.get(full_endpoint_encoded, headers=headers, timeout=10)
            results["GET_encoded_endpoint"] = {
                "status": encoded_response.status_code,
                "success": encoded_response.status_code < 400,
                "endpoint": full_endpoint_encoded,
                "note": "Testing with URL-encoded curly braces like in curl example"
            }
            
    except Exception as e:
        results["GET_full_contact"] = {"error": str(e)}
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "discovery": "Found /full endpoint and correct user3 location: investorData.userFields.user3",
        "test_results": results,
        "next_step": "If this works, we can build the full sync script!"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
