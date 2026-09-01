"""
Quick test script to confirm the service account can read/write the Google Sheet.
Run this once to validate credentials before building the real pipeline.
"""
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def main():
    if not SHEET_ID:
        raise RuntimeError("GOOGLE_SHEET_ID is not set in .env")
    if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise RuntimeError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(SHEET_ID).sheet1
    rows = sheet.get_all_records()

    print(f"Connected successfully. Found {len(rows)} data row(s):")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()