from flask import Flask, request, jsonify
import csv
import os
import requests

app = Flask(__name__)

REALNEX_API_BASE = "https://sync.realnex.com/api/v1"
API_KEY = os.getenv("REALNEX_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

@app.route("/")
def root():
    return "✅ RealNex GPT Sync is live!", 200

@app.route("/noop")
def noop():
    return "noop", 200

@app.route("/upload", methods=["PUT"])
def upload_csv():
    try:
        data = request.get_data()
        with open("/mnt/data/Merged_Contact_Scores.csv", "wb") as f:
            f.write(data)
        return "Upload successful", 200
    except Exception as e:
        return f"Upload failed: {str(e)}", 500

@app.route("/batch_push", methods=["POST"])
def batch_push():
    file_path = "/mnt/data/Merged_Contact_Scores.csv"
    if not os.path.exists(file_path):
        return "CSV file not found", 404

    updates = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            contact_id = row.get("ContactKey")
            if not contact_id:
                continue
            payload = {
                "userFields": {
                    "user3": row.get("GPT Score", ""),
                    "user4": row.get("Next Action", ""),
                    "user8": row.get("Last Scored", "")
                }
            }
            updates.append((contact_id, payload))

    # Push in batches of 99
    failures = []
    for i in range(0, len(updates), 99):
        batch = updates[i:i+99]
        for contact_id, payload in batch:
            url = f"{REALNEX_API_BASE}/Crm/contact/{contact_id}"
            response = requests.put(url, json=payload, headers=HEADERS)
            if response.status_code != 200:
                failures.append({
                    "contact_id": contact_id,
                    "status_code": response.status_code,
                    "response": response.text
                })

    return jsonify({
        "total": len(updates),
        "failures": failures,
        "success": len(updates) - len(failures)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
