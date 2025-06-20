import os
import requests
import pandas as pd
from io import StringIO
from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables
REALNEX_API_KEY = os.getenv('REALNEX_API_KEY')
REALNEX_SELECTED_DB = os.getenv('REALNEX_SELECTED_DB')
GOOGLE_DRIVE_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID') or "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"

# Use the CORRECT API base URL (OData endpoint)
REALNEX_API_BASE = "https://sync.realnex.com/api/v1/CrmOData"

def download_csv(file_id: str) -> pd.DataFrame:
    """Download CSV from Google Drive"""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))

def get_contact_by_key(contact_key: str) -> dict:
    """Get contact details to verify it exists"""
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Search for contact by key
    url = f"{REALNEX_API_BASE}/Contacts"
    params = {
        "$filter": f"contactKey eq '{contact_key}'",
        "$top": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Contact lookup: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("value", [])
            if contacts:
                return contacts[0]
        
        return None
    except Exception as e:
        logger.error(f"Error looking up contact: {e}")
        return None

def update_contact_odata(contact_key: str, user3_value: str) -> dict:
    """Update contact using OData endpoint (PATCH method)"""
    
    # First, get the contact to find its ID
    contact = get_contact_by_key(contact_key)
    if not contact:
        return {
            "contact": contact_key,
            "success": False,
            "message": "Contact not found"
        }
    
    contact_id = contact.get("contactId")
    if not contact_id:
        return {
            "contact": contact_key,
            "success": False,
            "message": "Contact ID not found"
        }
    
    # Update using OData PATCH method
    url = f"{REALNEX_API_BASE}/Contacts({contact_id})"
    
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Payload for updating user3 field
    payload = {
        "user3": user3_value
    }
    
    try:
        logger.info(f"Updating contact {contact_key} (ID: {contact_id}) with score {user3_value}")
        response = requests.patch(url, json=payload, headers=headers, timeout=30)
        
        logger.info(f"Update response: {response.status_code}")
        
        if response.status_code in [200, 204]:  # 200 OK or 204 No Content = success
            return {
                "contact": contact_key,
                "score": user3_value,
                "success": True,
                "status": response.status_code,
                "message": "Successfully updated"
            }
        else:
            return {
                "contact": contact_key,
                "success": False,
                "status": response.status_code,
                "message": response.text[:200]
            }
            
    except Exception as e:
        logger.error(f"Exception updating contact: {e}")
        return {
            "contact": contact_key,
            "success": False,
            "message": str(e)
        }

def run_sync() -> dict:
    """Main sync function"""
    if not REALNEX_API_KEY:
        return {"error": "Missing REALNEX_API_KEY"}
    
    try:
        logger.info(f"Downloading CSV from file ID: {GOOGLE_DRIVE_FILE_ID}")
        df = download_csv(GOOGLE_DRIVE_FILE_ID)
        logger.info(f"Downloaded {len(df)} rows")
    except Exception as e:
        logger.error(f"CSV download failed: {e}")
        return {"error": f"CSV download failed: {str(e)}"}
    
    if "contact_key" not in df.columns or "GPT Score" not in df.columns:
        return {"error": "CSV must contain 'contact_key' and 'GPT Score' columns"}
    
    # Process first 5 contacts as a test
    test_contacts = df.head(5)
    results = []
    success_count = 0
    
    for _, row in test_contacts.iterrows():
        contact_key = str(row["contact_key"]).strip()
        score = row["GPT Score"]
        
        if contact_key and pd.notna(score):
            result = update_contact_odata(contact_key, str(score))
            results.append(result)
            
            if result["success"]:
                success_count += 1
                logger.info(f"✅ Updated {contact_key} with score {score}")
            else:
                logger.error(f"❌ Failed {contact_key}: {result['message']}")
    
    return {
        "test_mode": True,
        "contacts_tested": len(results),
        "successful_updates": success_count,
        "failed_updates": len(results) - success_count,
        "results": results,
        "message": f"Test completed: {success_count}/{len(results)} successful. Using OData endpoint."
    }

def test_odata_connectivity() -> dict:
    """Test OData API connectivity"""
    if not REALNEX_API_KEY:
        return {"error": "Missing REALNEX_API_KEY"}
    
    headers = {
        "Authorization": f"Bearer {REALNEX_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Test getting contacts (like your friend's code)
        url = f"{REALNEX_API_BASE}/Contacts"
        params = {"$top": 1}  # Just get 1 contact to test
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        return {
            "odata_endpoint": url,
            "status": response.status_code,
            "success": response.status_code == 200,
            "response_sample": response.json() if response.status_code == 200 else response.text[:200],
            "message": "OData connectivity test"
        }
        
    except Exception as e:
        return {"error": str(e)}

# Flask routes
@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "RealNex Sync Service - Using OData Endpoint",
        "endpoints": {
            "/test": "Check configuration",
            "/run": "Test contact updates with OData",
            "/debug": "Test OData connectivity"
        }
    })

@app.route("/test", methods=["GET"])
def test_config():
    """Test configuration"""
    return jsonify({
        "realnex_api_key": "✅ Present" if REALNEX_API_KEY else "❌ Missing",
        "drive_file_id": f"✅ Using: {GOOGLE_DRIVE_FILE_ID}",
        "api_base": REALNEX_API_BASE,
        "note": "Now using OData endpoint (like your friend's working code)"
    })

@app.route("/run", methods=["GET"])
def trigger_run():
    """Trigger the sync process using OData"""
    logger.info("Sync process triggered via /run endpoint - using OData")
    result = run_sync()
    return jsonify(result)

@app.route("/debug", methods=["GET"])
def debug_odata():
    """Test OData API connectivity"""
    result = test_odata_connectivity()
    return jsonify(result)

if __name__ == "__main__":
    # Use PORT environment variable for Render compatibility
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
