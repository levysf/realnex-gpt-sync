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
        full_response = requests.get(full_endpoint, headers=merge_patch_headers, timeout=15)
        results["GET_full_contact"] = {
            "status": full_response.status_code,
            "success": full_response.status_code < 400
        }
        
        if full_response.status_code < 400:
            full_contact_data = full_response.json()
            
            # Test different field types to see which ones work/are faster
            test_fields = [
                {
                    "name": "title",
                    "payload": {"title": "UPDATED-TITLE-TEST"},
                    "description": "Simple string field"
                },
                {
                    "name": "mobile", 
                    "payload": {"mobile": "+1 (415) 555-MOBILE"},
                    "description": "Phone number field"
                },
                {
                    "name": "email",
                    "payload": {"email": "test-update@example.com"},
                    "description": "Email field"
                },
                {
                    "name": "fax",
                    "payload": {"fax": "415-555-FAX"},
                    "description": "Fax field (what we want for GPT scores)"
                },
                {
                    "name": "doNotCall",
                    "payload": {"doNotCall": True},
                    "description": "Boolean field"
                }
            ]
            
            # Test each field with a shorter timeout first
            for test in test_fields:
                field_name = test["name"]
                try:
                    response = requests.put(
                        regular_endpoint, 
                        headers=merge_patch_headers, 
                        json=test["payload"], 
                        timeout=20
                    )
                    results[f"PUT_{field_name}"] = {
                        "status": response.status_code,
                        "success": response.status_code < 400,
                        "field": field_name,
                        "description": test["description"],
                        "body_preview": response.text[:300] if response.text else "",
                        "payload_sent": test["payload"]
                    }
                    
                    # If we get a success, stop and verify it worked
                    if response.status_code < 400:
                        results[f"SUCCESS_FOUND"] = {
                            "successful_field": field_name,
                            "next_step": "This field type works! We can use this pattern."
                        }
                        break
                        
                except requests.exceptions.Timeout:
                    results[f"PUT_{field_name}"] = {
                        "status": "TIMEOUT",
                        "field": field_name,
                        "description": test["description"],
                        "note": f"Timed out after 20 seconds"
                    }
                except Exception as e:
                    results[f"PUT_{field_name}"] = {
                        "status": "ERROR",
                        "field": field_name,
                        "error": str(e)
                    }
            
            # If we found a working field, test the nested user3 field
            if "SUCCESS_FOUND" in results:
                try:
                    user3_patch = {
                        "investorData": {
                            "userFields": {
                                "user3": "GPT-SCORE-NESTED-TEST"
                            }
                        }
                    }
                    user3_response = requests.put(regular_endpoint, headers=merge_patch_headers, json=user3_patch, timeout=25)
                    results["PUT_user3_nested"] = {
                        "status": user3_response.status_code,
                        "success": user3_response.status_code < 400,
                        "body_preview": user3_response.text[:300] if user3_response.text else "",
                        "approach": "Nested investorData.userFields.user3 update"
                    }
                except requests.exceptions.Timeout:
                    results["PUT_user3_nested"] = {
                        "status": "TIMEOUT", 
                        "note": "Nested field update timed out"
                    }
                except Exception as e:
                    results["PUT_user3_nested"] = {"error": str(e)}
            
    except Exception as e:
        results["GET_full_contact"] = {"error": str(e)}
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "strategy": "Testing multiple field types to find which ones update successfully",
        "test_results": results,
        "goal": "Find a field type that works quickly, then apply same pattern to user3"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
