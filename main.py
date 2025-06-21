import csv
import os
import requests
import time

REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
API_URL = "https://sync.realnex.com/api/v1/Crm/contact"

HEADERS = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Content-Type": "application/merge-patch+json",
    "Accept": "application/json;odata.metadata=minimal;odata.streaming=true"
}

def update_fax_field(contact_key, score):
    url = f"{API_URL}/{contact_key}"
    payload = {
        "fax": str(score)
    }

    response = requests.put(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Updated {contact_key} with score {score}")
    else:
        print(f"❌ Failed for {contact_key}: {response.status_code} | {response.text}")

def process_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            contact_key = row.get("contact_key")
            score = row.get("GPT Score")
            if contact_key and score and score != "" and float(score) >= 10:
                update_fax_field(contact_key, score)
                time.sleep(0.4)  # throttle to avoid hitting rate limits
            else:
                print(f"⏩ Skipping {contact_key} with score {score}")

if __name__ == "__main__":
    csv_path = "scored_contacts.csv"  # replace with your actual filename
    process_csv(csv_path)