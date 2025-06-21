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
    # Use the merge-patch+json Content-Type from Swagger docs
    merge_patch_headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Content-Type": "application/merge-patch+json",
        "Accept": "application/json"
    }
    
    regular_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}"
    full_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}/full"
    
    results = {}
    
    # Get the full contact data first
    try:
        full_response = requests.get(full_endpoint, headers=merge_patch_headers, timeout=10)
        results["GET_full_contact"] = {
            "status": full_response.status_code,
            "success": full_response.status_code < 400
        }
        
        if full_response.status_code < 400:
            full_contact_data = full_response.json()
            
            # Test 1: Update fax field with merge-patch+json
            fax_patch = {"fax": "415-555-MERGE-PATCH"}
            fax_response = requests.put(regular_endpoint, headers=merge_patch_headers, json=fax_patch, timeout=10)
            results["PUT_fax_merge_patch"] = {
                "status": fax_response.status_code,
                "success": fax_response.status_code < 400,
                "body_preview": fax_response.text[:500] if fax_response.text else "",
                "approach": "PUT with application/merge-patch+json for fax"
            }
            
            # Test 2: Update user3 field in correct nested structure
            user3_patch = {
                "investorData": {
                    "userFields": {
                        "user3": "GPT-SCORE-MERGE-PATCH"
                    }
                }
            }
            user3_response = requests.put(regular_endpoint, headers=merge_patch_headers, json=user3_patch, timeout=10)
            results["PUT_user3_merge_patch"] = {
                "status": user3_response.status_code,
                "success": user3_response.status_code < 400,
                "body_preview": user3_response.text[:500] if user3_response.text else "",
                "approach": "PUT with application/merge-patch+json for user3",
                "current_user3": full_contact_data.get("investorData", {}).get("userFields", {}).get("user3")
            }
            
            # Test 3: Try PATCH method with merge-patch+json
            patch_response = requests.patch(regular_endpoint, headers=merge_patch_headers, json=fax_patch, timeout=10)
            results["PATCH_merge_patch"] = {
                "status": patch_response.status_code,
                "success": patch_response.status_code < 400,
                "body_preview": patch_response.text[:500] if patch_response.text else "",
                "approach": "PATCH with application/merge-patch+json"
            }
            
            # Test 4: Try updating both fields at once
            combined_patch = {
                "fax": "415-555-COMBINED",
                "investorData": {
                    "userFields": {
                        "user3": "COMBINED-USER3-TEST"
                    }
                }
            }
            combined_response = requests.put(regular_endpoint, headers=merge_patch_headers, json=combined_patch, timeout=10)
            results["PUT_combined_merge_patch"] = {
                "status": combined_response.status_code,
                "success": combined_response.status_code < 400,
                "body_preview": combined_response.text[:500] if combined_response.text else "",
                "approach": "PUT both fax and user3 with merge-patch+json"
            }
            
    except Exception as e:
        results["error"] = str(e)
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "discovery": "Found application/merge-patch+json Content-Type in Swagger docs!",
        "test_results": results,
        "expectation": "This should finally work with merge-patch+json Content-Type!"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
