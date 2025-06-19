import requests
import datetime
import os
import pandas as pd
import time

REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
BASE_URL = "https://sync.realnex.com/api/v1/CrmOData"
CSV_FILE = "Merged_Contact_Scores.csv"

HEADERS = {
    "Authorization": f"Bearer {REALNEX_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def update_contact_score(contact_key, score, next_action, date_str):
    url = f"{BASE_URL}/Contacts(guid'{contact_key}')"
    body = {
        "user_3": str(score),
        "user_4": next_action,
        "user_8": date_str
    }
    res = requests.patch(url, headers=HEADERS, json=body)
    return res.status_code, res.text

def main():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    df = pd.read_csv(CSV_FILE)
    updated = []

    for _, row in df.iterrows():
        contact_key = row.get("contact_key", "").strip("{}")
        score = row.get("total_score", 0)

        if not contact_key or pd.isna(score):
            continue

        status, msg = update_contact_score(
            contact_key,
            round(score, 2),
            "Scored via GPT",
            today
        )

        print(f"Updated {row['contact_name']} ({contact_key}): {status}")
        updated.append((row['contact_name'], status, msg))

    print(f"\n✅ Finished one batch: {len(updated)} contacts pushed.")

if __name__ == "__main__":
    start = time.time()
    while time.time() - start < 1200:  # 20 minutes
        main()
        print("Sleeping 5 seconds...\n")
        time.sleep(5)
