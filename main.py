from flask import Flask, request, jsonify
import os
import csv
import requests
import time

app = Flask(__name__)

UPLOAD_FILENAME = "uploaded.csv"
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

# Ensure API key is available
if not REALNEX_API_KEY:
    raise RuntimeError("REALNEX_API_KEY environment variable is required")

@app.route("/", methods=["GET"])
def index():
    return "✅ RealNex GPT Sync is live.", 200

@app.route("/upload", methods=["PUT"])
def upload_file():
    try:
        with open(UPLOAD_FILENAME, "wb") as f:
            f.write(request.data)
        return "✅ Upload successful", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(UPLOAD_FILENAME):
        return jsonify({"error": f"CSV file not found: {UPLOAD_FILENAME}"}), 400

    results = []

    with open(UPLOAD_FILENAME, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        valid_rows = []

        for row in reader:
            contact_key = row.get("contact_key", "").strip()
            if contact_key:
                payload = {
                    "user3": row.get("GPT Score", "").strip(),
                    "user4": row.get("Next Action", "").strip(),
                    "user8": row.get("Last Scored", "").strip()
                }
                valid_rows.append((contact_key, payload))

    for i, (contact_key, payload) in enumerate(valid_rows):
        url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}"
        headers = {
            "Authorization": f"Bearer {REALNEX_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.put(url, json=payload, headers=headers)
            results.append({
                "contact_key": contact_key,
                "status": response.status_code,
                "body": response.text
            })
        except Exception as e:
            results.append({
                "contact_key": contact_key,
                "error": str(e)
            })

        # throttle after 100 requests
        if (i + 1) % 100 == 0:
            time.sleep(1)

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
