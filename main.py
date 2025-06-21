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
    # Test different base URLs and approaches
    base_urls = [
        "https://sync.realnex.com",
        "https://api.realnex.com", 
        "https://app.realnex.com",
        "https://www.realnex.com"
    ]
    
    results = {}
    
    # First, let's try some simple GET requests to see what's available
    for i, base_url in enumerate(base_urls):
        base_name = f"base_{i+1}"
        results[base_name] = {"base_url": base_url}
        
        # Try some common endpoints
        test_endpoints = [
            f"{base_url}/",
            f"{base_url}/api",
            f"{base_url}/v1",
            f"{base_url}/api/v1",
            f"{base_url}/swagger",
            f"{base_url}/docs"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code < 400:
                    results[base_name][f"working_endpoint"] = {
                        "url": endpoint,
                        "status": response.status_code,
                        "content_preview": response.text[:100] if response.text else ""
                    }
                    break
            except:
                continue
    
    # Also test our contact endpoint with different HTTP methods
    contact_tests = {}
    test_url = f"https://sync.realnex.com/api/v1/contact/{REALNEX_CONTACT_ID}"
    
    # Try GET first to see if contact exists
    try:
        get_response = requests.get(test_url, headers=headers, timeout=10)
        contact_tests["GET"] = {
            "status_code": get_response.status_code,
            "body": get_response.text[:200] if get_response.text else ""
        }
    except Exception as e:
        contact_tests["GET"] = {"error": str(e)}
    
    # Try PATCH instead of PUT
    try:
        patch_response = requests.patch(test_url, headers=headers, json={"fax": "415-555-0000"}, timeout=10)
        contact_tests["PATCH"] = {
            "status_code": patch_response.status_code,
            "body": patch_response.text[:200] if patch_response.text else ""
        }
    except Exception as e:
        contact_tests["PATCH"] = {"error": str(e)}
    
    # Try POST 
    try:
        post_response = requests.post(test_url, headers=headers, json={"fax": "415-555-0000"}, timeout=10)
        contact_tests["POST"] = {
            "status_code": post_response.status_code,
            "body": post_response.text[:200] if post_response.text else ""
        }
    except Exception as e:
        contact_tests["POST"] = {"error": str(e)}
    
    return {
        "contact_id": REALNEX_CONTACT_ID,
        "api_key_present": bool(REALNEX_API_KEY),
        "api_key_length": len(REALNEX_API_KEY) if REALNEX_API_KEY else 0,
        "base_url_tests": results,
        "contact_method_tests": contact_tests,
        "headers_used": {
            "Authorization": f"Bearer {REALNEX_API_KEY[:10]}..." if REALNEX_API_KEY else "None",
            "Content-Type": headers.get("Content-Type"),
            "accept": headers.get("accept")
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
