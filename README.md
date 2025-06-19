# RealNex GPT Sync

This Flask application uploads a CSV file of contact scores and pushes them to the RealNex Sync API.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set `REALNEX_API_KEY` with your API token.

## Usage

1. Start the server:
   ```bash
   python main.py
   ```
2. Upload your CSV file with a `PUT` request to `/upload`:
   ```bash
   curl -X PUT --data-binary @Merged_Contact_Scores.csv http://localhost:10000/upload
   ```
3. Trigger the batch push:
   ```bash
   curl -X POST http://localhost:10000/batch_push
   ```

The batch push processes contacts in groups of up to 100 requests to comply with RealNex's rate limits.
