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
    # Based on Swagger docs: GET/PUT /api/v1/Crm/contact/{contactKey}
    correct_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}"
    
    results = {}
    
    print(f"Testing correct endpoint: {correct_endpoint}")
    
    # First, try GET to see if contact exists
    try:
        get_response = requests.get(correct_endpoint, headers=headers, timeout=10)
        results["GET_contact"] = {
            "url": correct_endpoint,
            "status": get_response.status_code,
            "body_preview": get_response.text[:500] if get_response.text else "",
            "success": get_response.status_code < 400
        }
        
        # If GET works, try PUT with the full contact object
        if get_response.status_code < 400:
            # Parse the existing contact data
            try:
                contact_data = get_response.json()
                
                # Update fax field in the full contact object
                contact_data["fax"] = "415-555-0000"
                put_fax_response = requests.put(correct_endpoint, headers=headers, json=contact_data, timeout=10)
                results["PUT_fax_full_object"] = {
                    "status": put_fax_response.status_code,
                    "body_preview": put_fax_response.text[:500] if put_fax_response.text else "",
                    "success": put_fax_response.status_code < 400,
                    "approach": "Sent full contact object with updated fax"
                }
                
                # Reset and try user_3 field
                contact_data = get_response.json()  # Reset to original
                contact_data["user_3"] = "TESTING USER 3 FIELD"
                put_user3_response = requests.put(correct_endpoint, headers=headers, json=contact_data, timeout=10)
                results["PUT_user_3_full_object"] = {
                    "status": put_user3_response.status_code,
                    "body_preview": put_user3_response.text[:500] if put_user3_response.text else "",
                    "success": put_user3_response.status_code < 400,
                    "approach": "Sent full contact object with user_3 field"
                }
                
            except Exception as json_error:
                results["json_parse_error"] = str(json_error)
            
            # Also try with different headers
            alt_headers = {
                "Authorization": f"Bearer {REALNEX_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            put_alt_payload = {"fax": "415-555-2222"}
            put_alt_response = requests.put(correct_endpoint, headers=alt_headers, json=put_alt_payload, timeout=10)
            results["PUT_with_alt_headers"] = {
                "status": put_alt_response.status_code,
                "body_preview": put_alt_response.text[:500] if put_alt_response.text else "",
                "success": put_alt_response.status_code < 400,
                "headers_used": alt_headers,
                "payload_sent": put_alt_payload
            }
        
    except Exception as e:
        results["GET_contact"] = {
            "url": correct_endpoint,
            "error": str(e)
        }
    
    # Also test the base CRM endpoint to see what's available
    base_crm_endpoint = "https://sync.realnex.com/api/v1/Crm"
    try:
        base_response = requests.get(base_crm_endpoint, headers=headers, timeout=10)
        results["base_crm_endpoint"] = {
            "url": base_crm_endpoint,
            "status": base_response.status_code,
            "body_preview": base_response.text[:300] if base_response.text else ""
        }
    except Exception as e:
        results["base_crm_endpoint"] = {"error": str(e)}
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "correct_endpoint_found": "YES - /api/v1/Crm/contact/{contactKey}",
        "test_results": results,
        "summary": {
            "endpoint_used": correct_endpoint,
            "expecting": "200 status codes for GET and PUT operations"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
