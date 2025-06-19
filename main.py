import os
import pandas as pd
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB file upload limit

REALNEX_API_KEY = os.environ.get("REALNEX_API_KEY")
REALNEX_API_BASE = "https://api.realnex.com/api/v1"

uploaded_file_path = "uploaded_scores.csv"

@app.route("/upload", methods=["PUT"])
def upload_file():
    file = request.data
    with open(uploaded_file_path, "wb") as f:
        f.write(file)
    return "Upload successful"

@app.route("/batch_push", methods=["POST"])
def batch_push():
    if not os.path.exists(uploaded_file_path):
        return jsonify({"error": "No uploaded file found"}), 400

    df = pd.read_csv(uploaded_file_path)
    results = []

    for _, row in df.iterrows():
        contact_key = row.get("contact_key")
        if pd.isna(contact_key):
            continue

        payload = {
            "user_3": row.get("GPT Score", ""),
            "user_4": row.get("Next Action", ""),
            "user_8": row.get("Last Scored", ""),
        }

        url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {REALNEX_API_KEY}",
        }

        response = requests.put(url, headers=headers, json=payload)

        results.append({
            "contact_key": contact_key,
            "status": response.status_code,
            "body": response.text
        })

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
