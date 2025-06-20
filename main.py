import os
import csv
import requests
import pandas as pd
import io

REALNEX_API_TOKEN = os.getenv('REALNEX_API_TOKEN') or os.getenv('REALNEX_API_KEY')
REALNEX_API_BASE = "https://sync.realnex.com/api/v1"
GOOGLE_DRIVE_FILE_ID = "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"

def download_csv(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text))

def update_contact(contact_key: str, user3_value: str) -> requests.Response:
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SelectedDb-Key": "c8fc1bac-3987-45b7-ba91-3551921b1f1a"
    }
    payload = {
        "userFields": {
            "user3": user3_value
        }
    }
    return requests.put(url, json=payload, headers=headers)

def main():
    if not REALNEX_API_TOKEN:
        raise SystemExit("REALNEX_API_TOKEN environment variable not set")

    df = download_csv(GOOGLE_DRIVE_FILE_ID)

    if "contact_key" not in df.columns or "GPT Score" not in df.columns:
        raise SystemExit("CSV must contain 'contact_key' and 'GPT Score' columns")

    for _, row in df.iterrows():
        contact_key = str(row["contact_key"]).strip()
        score = row["GPT Score"]
        if contact_key and pd.notna(score):
            resp = update_contact(contact_key, str(score))
            if resp.status_code >= 400:
                print(f"Failed to update {contact_key}: {resp.status_code} {resp.text}")
            else:
                print(f"Updated {contact_key}")

if __name__ == "__main__":
    main()
