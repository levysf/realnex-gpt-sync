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
    
    # Get the full contact data first (with shorter timeout since this works)
    try:
        full_response = requests.get(full_endpoint, headers=merge_patch_headers, timeout=15)
        results["GET_full_contact"] = {
            "status": full_response.status_code,
            "success": full_response.status_code < 400
        }
        
        if full_response.status_code < 400:
            full_contact_data = full_response.json()
            current_user3 = full_contact_data.get("investorData", {}).get("userFields", {}).get("user3", "unknown")
            
            # Test 1: Simple fax update with longer timeout
            try:
                fax_patch = {"fax": "415-555-MERGE-PATCH"}
                fax_response = requests.put(regular_endpoint, headers=merge_patch_headers, json=fax_patch, timeout=30)
                results["PUT_fax_merge_patch"] = {
                    "status": fax_response.status_code,
                    "success": fax_response.status_code < 400,
                    "body_preview": fax_response.text[:500] if fax_response.text else "",
                    "approach": "PUT with application/merge-patch+json for fax"
                }
            except requests.exceptions.Timeout:
                results["PUT_fax_merge_patch"] = {
                    "status": "TIMEOUT",
                    "note": "Request timed out after 30 seconds - may still be processing"
                }
            except Exception as e:
                results["PUT_fax_merge_patch"] = {"error": str(e)}
            
            # Test 2: User3 update (only if fax didn't timeout)
            if "PUT_fax_merge_patch" in results and results["PUT_fax_merge_patch"].get("status") != "TIMEOUT":
                try:
                    user3_patch = {
                        "investorData": {
                            "userFields": {
                                "user3": "GPT-SCORE-SUCCESS"
                            }
                        }
                    }
                    user3_response = requests.put(regular_endpoint, headers=merge_patch_headers, json=user3_patch, timeout=30)
                    results["PUT_user3_merge_patch"] = {
                        "status": user3_response.status_code,
                        "success": user3_response.status_code < 400,
                        "body_preview": user3_response.text[:500] if user3_response.text else "",
                        "approach": "PUT with application/merge-patch+json for user3",
                        "current_user3_before_update": current_user3
                    }
                except requests.exceptions.Timeout:
                    results["PUT_user3_merge_patch"] = {
                        "status": "TIMEOUT",
                        "note": "Request timed out after 30 seconds - may still be processing"
                    }
                except Exception as e:
                    results["PUT_user3_merge_patch"] = {"error": str(e)}
            
            # Test 3: Verify the update worked by getting the contact again
            if any(test.get("success") for test in results.values() if isinstance(test, dict)):
                try:
                    verify_response = requests.get(full_endpoint, headers=merge_patch_headers, timeout=15)
                    if verify_response.status_code < 400:
                        updated_contact = verify_response.json()
                        results["verification"] = {
                            "status": verify_response.status_code,
                            "updated_fax": updated_contact.get("fax"),
                            "updated_user3": updated_contact.get("investorData", {}).get("userFields", {}).get("user3"),
                            "original_user3": current_user3
                        }
                except Exception as e:
                    results["verification"] = {"error": str(e)}
            
    except Exception as e:
        results["GET_full_contact"] = {"error": str(e)}
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "discovery": "Testing merge-patch+json with longer timeouts",
        "test_results": results,
        "note": "Timeout suggests server is processing the request (good sign!)"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
