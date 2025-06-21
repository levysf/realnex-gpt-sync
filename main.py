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
    # Use the working full endpoint
    full_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}/full"
    regular_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}"
    
    # Try the special headers from the curl example
    odata_headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "accept": "application/json;odata.metadata=minimal;odata.streaming=true",
        "Content-Type": "application/json"
    }
    
    results = {}
    
    # Get the full contact data
    try:
        full_response = requests.get(full_endpoint, headers=odata_headers, timeout=10)
        results["GET_full_contact"] = {
            "status": full_response.status_code,
            "success": full_response.status_code < 400
        }
        
        if full_response.status_code < 400:
            full_contact_data = full_response.json()
            
            # Test 1: Try PUT with OData headers
            test_contact = full_contact_data.copy()
            test_contact["fax"] = "415-555-ODATA"
            
            odata_put_response = requests.put(regular_endpoint, headers=odata_headers, json=test_contact, timeout=10)
            results["PUT_with_odata_headers"] = {
                "status": odata_put_response.status_code,
                "success": odata_put_response.status_code < 400,
                "body_preview": odata_put_response.text[:500] if odata_put_response.text else ""
            }
            
            # Test 2: Try PATCH instead of PUT
            patch_data = {"fax": "415-555-PATCH"}
            patch_response = requests.patch(regular_endpoint, headers=odata_headers, json=patch_data, timeout=10)
            results["PATCH_with_odata"] = {
                "status": patch_response.status_code,
                "success": patch_response.status_code < 400,
                "body_preview": patch_response.text[:500] if patch_response.text else ""
            }
            
            # Test 3: Try POST to the regular endpoint
            post_contact = full_contact_data.copy()
            post_contact["investorData"]["userFields"]["user3"] = "POST-TEST-USER3"
            
            post_response = requests.post(regular_endpoint, headers=odata_headers, json=post_contact, timeout=10)
            results["POST_with_user3_update"] = {
                "status": post_response.status_code,
                "success": post_response.status_code < 400,
                "body_preview": post_response.text[:500] if post_response.text else ""
            }
            
            # Test 4: Check if there's a different update endpoint
            update_endpoints = [
                f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}/update",
                f"https://sync.realnex.com/api/v1/Crm/contact/update/{REALNEX_CONTACT_ID}",
                f"https://sync.realnex.com/api/v1/Crm/updatecontact/{REALNEX_CONTACT_ID}"
            ]
            
            update_results = {}
            for endpoint in update_endpoints:
                try:
                    update_response = requests.post(endpoint, headers=odata_headers, json={"fax": "415-UPDATE-TEST"}, timeout=10)
                    update_results[endpoint] = {
                        "status": update_response.status_code,
                        "success": update_response.status_code < 400
                    }
                except:
                    update_results[endpoint] = {"error": "Request failed"}
            
            results["update_endpoint_tests"] = update_results
            
            # Test 5: Try minimal payload that just includes the ID and changed field
            minimal_payload = {
                "key": full_contact_data["key"],
                "fax": "415-MINIMAL"
            }
            
            minimal_response = requests.put(regular_endpoint, headers=odata_headers, json=minimal_payload, timeout=10)
            results["PUT_minimal_payload"] = {
                "status": minimal_response.status_code,
                "success": minimal_response.status_code < 400,
                "body_preview": minimal_response.text[:500] if minimal_response.text else ""
            }
            
    except Exception as e:
        results["error"] = str(e)
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "test_results": results,
        "status": "Testing different HTTP methods and headers to find working update approach"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
