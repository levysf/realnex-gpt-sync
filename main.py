import os
import requests
import pandas as pd
from io import StringIO
from flask import Flask, jsonify
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables
REALNEX_API_TOKEN = os.getenv('REALNEX_API_KEY')
REALNEX_SELECTED_DB = os.getenv('REALNEX_SELECTED_DB')
GOOGLE_DRIVE_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID') or "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"

REALNEX_API_BASE = "https://sync.realnex.com/api/v1"

def download_csv(file_id: str) -> pd.DataFrame:
    """Download CSV from Google Drive"""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))

def build_minimal_payload(user3_value: str) -> dict:
    """Build minimal payload - sometimes less is more"""
    return {
        "userFields": {
            "user3": user3_value
        }
    }

def build_full_payload(user3_value: str) -> dict:
    """Build full payload"""
    return {
        "broker": False,
        "rehabs": False,
        "jointVenture": False,
        "tripleNet": False,
        "singleTenant": False,
        "multipleTenant": False,
        "singleFamily": False,
        "creditTenant": False,
        "userFields": {
            "user3": user3_value
        },
        "logicalFields": {f"logical{i}": False for i in range(1, 25)}
    }

def update_contact_comprehensive(contact_key: str, user3_value: str) -> dict:
    """Try multiple approaches to fix 415 error"""
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    
    # Different strategies to try
    strategies = [
        {
            "name": "Minimal JSON with PUT",
            "method": "PUT",
            "headers": {
                "Authorization": f"Bearer {REALNEX_API_TOKEN}",
                "Content-Type": "application/json",
                "X-SelectedDb-Key": REALNEX_SELECTED_DB
            },
            "payload": build_minimal_payload(user3_value),
            "send_as": "json"
        },
        {
            "name": "Minimal JSON with POST",
            "method": "POST", 
            "headers": {
                "Authorization": f"Bearer {REALNEX_API_TOKEN}",
                "Content-Type": "application/json",
                "X-SelectedDb-Key": REALNEX_SELECTED_DB
            },
            "payload": build_minimal_payload(user3_value),
            "send_as": "json"
        },
        {
            "name": "Form data",
            "method": "PUT",
            "headers": {
                "Authorization": f"Bearer {REALNEX_API_TOKEN}",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-SelectedDb-Key": REALNEX_SELECTED_DB
            },
            "payload": {"userFields.user3": user3_value},
            "send_as": "form"
        },
        {
            "name": "No Content-Type header",
            "method": "PUT",
            "headers": {
                "Authorization": f"Bearer {REALNEX_API_TOKEN}",
                "X-SelectedDb-Key": REALNEX_SELECTED_DB
            },
            "payload": build_minimal_payload(user3_value),
            "send_as": "json"
        }
    ]
    
    for strategy in strategies:
        try:
            logger.info(f"Trying: {strategy['name']} for contact {contact_key}")
            
            if strategy["send_as"] == "json":
                if strategy["method"] == "PUT":
                    response = requests.put(url, json=strategy["payload"], headers=strategy["headers"], timeout=30)
                elif strategy["method"] == "POST":
                    response = requests.post(url, json=strategy["payload"], headers=strategy["headers"], timeout=30)
            elif strategy["send_as"] == "form":
                response = requests.put(url, data=strategy["payload"], headers=strategy["headers"], timeout=30)
            
            if response.status_code < 400:
                logger.info(f"✅ SUCCESS with {strategy['name']}")
                return {
                    "contact": contact_key,
                    "score": user3_value,
                    "success": True,
                    "status": response.status_code,
                    "strategy": strategy["name"]
                }
            else:
                logger.warning(f"❌ {strategy['name']} failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Exception with {strategy['name']}: {e}")
    
    return {
        "contact": contact_key,
        "score": user3_value,
        "success": False,
        "message": "All strategies failed"
    }

def run_sync() -> dict:
    """Main sync function"""
    if not REALNEX_API_TOKEN or not REALNEX_SELECTED_DB:
        return {"error": "Missing REALNEX_API_KEY or REALNEX_SELECTED_DB"}
    
    try:
        logger.info(f"Downloading CSV from file ID: {GOOGLE_DRIVE_FILE_ID}")
        df = download_csv(GOOGLE_DRIVE_FILE_ID)
        logger.info(f"Downloaded {len(df)} rows")
    except Exception as e:
        logger.error(f"CSV download failed: {e}")
        return {"error": f"CSV download failed: {str(e)}"}
    
    if "contact_key" not in df.columns or "GPT Score" not in df.columns:
        return {"error": "CSV must contain 'contact_key' and 'GPT Score' columns"}
    
    # Test with first contact only
    first_row = df.iloc[0]
    contact_key = str(first_row["contact_key"]).strip()
    score = first_row["GPT Score"]
    
    logger.info(f"Testing with first contact: {contact_key}")
    result = update_contact_comprehensive(contact_key, str(score))
    
    return {
        "test_mode": True,
        "contact_tested": contact_key,
        "result": result,
        "message": "This was a test with the first contact only. If successful, contact support to process all contacts."
    }

# Flask routes
@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "RealNex Sync Service is up and running",
        "endpoints": {
            "/test": "Check configuration",
            "/run": "Test first contact with multiple strategies",
            "/debug": "Debug API connectivity"
        }
    })

@app.route("/test", methods=["GET"])
def test_config():
    """Test configuration"""
    return jsonify({
        "realnex_api_key": "✅ Present" if REALNEX_API_TOKEN else "❌ Missing",
        "realnex_db": "✅ Present" if REALNEX_SELECTED_DB else "❌ Missing",
        "drive_file_id": f"✅ Using: {GOOGLE_DRIVE_FILE_ID}",
        "api_base": REALNEX_API_BASE
    })

@app.route("/run", methods=["GET"])
def trigger_run():
    """Trigger the sync process (test mode)"""
    logger.info("Sync process triggered via /run endpoint")
    result = run_sync()
    return jsonify(result)

@app.route("/debug", methods=["GET"])
def debug_api():
    """Debug API connectivity"""
    if not REALNEX_API_TOKEN or not REALNEX_SELECTED_DB:
        return jsonify({"error": "Missing credentials"})
    
    try:
        # Test basic API connectivity
        test_url = f"{REALNEX_API_BASE}/Crm/contact"
        headers = {
            "Authorization": f"Bearer {REALNEX_API_TOKEN}",
            "X-SelectedDb-Key": REALNEX_SELECTED_DB
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        
        return jsonify({
            "api_connectivity": f"Status: {response.status_code}",
            "response_headers": dict(response.headers),
            "message": "Basic API connectivity test"
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    # Use PORT environment variable for Render compatibility
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
