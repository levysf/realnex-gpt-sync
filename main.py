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
        
        # If GET works, try different approaches
        if get_response.status_code < 400:
            contact_data = get_response.json()
            
            # Approach 1: Try POST instead of PUT (some APIs use POST for updates)
            contact_data["fax"] = "415-555-0000"
            post_response = requests.post(correct_endpoint, headers=headers, json=contact_data, timeout=10)
            results["POST_full_object"] = {
                "status": post_response.status_code,
                "body_preview": post_response.text[:500] if post_response.text else "",
                "success": post_response.status_code < 400,
                "approach": "POST with full contact object"
            }
            
            # Approach 2: Try different Content-Type
            form_headers = {
                "Authorization": f"Bearer {REALNEX_API_KEY}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            form_data = {"fax": "415-555-3333"}
            form_response = requests.put(correct_endpoint, headers=form_headers, data=form_data, timeout=10)
            results["PUT_form_data"] = {
                "status": form_response.status_code,
                "body_preview": form_response.text[:500] if form_response.text else "",
                "success": form_response.status_code < 400,
                "approach": "PUT with form data"
            }
            
            # Approach 3: Try a different endpoint - maybe there's an update endpoint
            update_endpoint = f"https://sync.realnex.com/api/v1/Crm/contact/{REALNEX_CONTACT_ID}/update"
            update_response = requests.post(update_endpoint, headers=headers, json={"fax": "415-555-4444"}, timeout=10)
            results["POST_update_endpoint"] = {
                "status": update_response.status_code,
                "body_preview": update_response.text[:500] if update_response.text else "",
                "success": update_response.status_code < 400,
                "approach": "POST to /update endpoint"
            }
            
            # Approach 4: Check if we can get more detailed error info
            detailed_headers = {
                "Authorization": f"Bearer {REALNEX_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "RealNex-API-Test/1.0"
            }
            detailed_response = requests.put(correct_endpoint, headers=detailed_headers, json={"fax": "415-555-5555"}, timeout=10)
            results["PUT_detailed_headers"] = {
                "status": detailed_response.status_code,
                "body_preview": detailed_response.text[:500] if detailed_response.text else "",
                "success": detailed_response.status_code < 400,
                "approach": "PUT with detailed headers",
                "response_headers": dict(detailed_response.headers) if detailed_response.headers else {}
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
