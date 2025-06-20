import requests
import json
import pandas as pd
import os

# Load environment variables
REALNEX_API_TOKEN = os.getenv('REALNEX_API_TOKEN') or os.getenv('REALNEX_API_KEY')
REALNEX_SELECTED_DB = os.getenv('REALNEX_SELECTED_DB')  # Must be set for header
GOOGLE_DRIVE_FILE_ID = "1uQVIDe2Jmi8CqyJtQikXZhn8cuc03VOk"  # Replace with actual ID

REALNEX_API_BASE = "https://sync.realnex.com/api/v1"


def download_csv(file_id: str) -> pd.DataFrame:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(pd.compat.StringIO(response.text))


def build_full_payload(user3_value: str) -> dict:
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
            "user1": "norma.reay@yahoo.com",
            "user2": "nreay@aol.com",
            "user3": user3_value,
            "user7": "1(650) 568-9311",
            "user8": "1(417) 777-2484",
            "user9": "1(573) 748-5690",
            "user10": "1(905) 676-1695"
        },
        "logicalFields": {f"logical{i}": False for i in range(1, 25)}
    }


def update_contact(contact_key: str, user3_value: str) -> requests.Response:
    url = f"{REALNEX_API_BASE}/Crm/contact/{contact_key}/investor"
    headers = {
        "Authorization": f"Bearer {REALNEX_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-SelectedDb-Key": REALNEX_SELECTED_DB
    }
    payload = build_full_payload(user3_value)
    return requests.put(url, json=payload, headers=headers)


def main():
    if not REALNEX_API_TOKEN or not REALNEX_SELECTED_DB:
        raise SystemExit("Missing REALNEX_API_TOKEN or REALNEX_SELECTED_DB in environment")

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
                print(f"Updated {contact_key} → user3 = {score}")


if __name__ == "__main__":
    main()
