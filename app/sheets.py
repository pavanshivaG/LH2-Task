"""
Google Sheets read/write layer using the service account.
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

# Column layout in the sheet (1-indexed)
COL_COMPANY_NAME = 1
COL_DOMAIN = 2
COL_FIT_VERDICT = 3
COL_CONFIDENCE = 4
COL_FOLLOW_UP = 5
COL_LAST_PROCESSED = 6


def _get_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet():
    client = _get_client()
    return client.open_by_key(SHEET_ID).sheet1


def get_unprocessed_rows():
    """
    Returns a list of dicts: {row_number, company_name, domain}
    for rows where fit_verdict (column C) is empty - i.e. not yet processed.
    """
    sheet = get_sheet()
    all_values = sheet.get_all_values()  # includes header row at index 0

    unprocessed = []
    for idx, row in enumerate(all_values[1:], start=2):  # row 2 onward, 1-indexed
        company_name = row[0].strip() if len(row) > 0 else ""
        domain = row[1].strip() if len(row) > 1 else ""
        fit_verdict = row[2].strip() if len(row) > 2 else ""

        if company_name and not fit_verdict:
            unprocessed.append({
                "row_number": idx,
                "company_name": company_name,
                "domain": domain,
            })

    return unprocessed


def write_verdict_to_row(row_number: int, fit_verdict: str, confidence: float,
                          follow_up_question: str, timestamp: str):
    """
    Writes the verdict back into columns C-F of the given row.
    """
    sheet = get_sheet()
    sheet.update(
        range_name=f"C{row_number}:F{row_number}",
        values=[[fit_verdict, confidence, follow_up_question, timestamp]],
    )


if __name__ == "__main__":
    rows = get_unprocessed_rows()
    print(f"Found {len(rows)} unprocessed row(s):")
    for r in rows:
        print(r)