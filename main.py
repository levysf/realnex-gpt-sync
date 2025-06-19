from flask import Flask, request, jsonify
import csv
import os
import requests

app = Flask(__name__)

REALNEX_API_BASE = "https://sync.realnex.com/api/v1"
API_KEY = os.getenv("REALNEX_API_KEY")
PORT = int(os.environ.get("PORT", 10000))  # Use env PORT or default to 10000

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
