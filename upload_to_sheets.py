import pandas as pd
import gspread
import google.auth
import os

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1piGYWlsdXF8cMDFxWI3h-T72vF-ef_hq-DL9HCxyLmA/edit#gid=828962645"
EXCEL_FILE = "backtest_results_2020-01-01_to_2025-01-01.xlsx"

def upload_to_google_sheets():
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: {EXCEL_FILE} does not exist.")
        return

    print("Authenticating with Google...")
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(credentials)

        print(f"Opening spreadsheet: {SPREADSHEET_URL}")
        sheet = client.open_by_url(SPREADSHEET_URL)
        worksheet = sheet.worksheet_by_id(828962645) # Or could just use sheet.get_worksheet_by_id

        print(f"Reading {EXCEL_FILE}...")
        df = pd.read_excel(EXCEL_FILE)
        
        # Fill NaN values with empty string for JSON serialization compatibility
        df = df.fillna("")
        
        # Convert dates to string format
        if 'Entry Date' in df.columns:
            df['Entry Date'] = df['Entry Date'].astype(str)

        print("Uploading data to Google Sheet...")
        # Clear existing data
        worksheet.clear()
        
        # Upload header and data
        data = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(values=data, range_name="A1")
        
        print("Formatting the spreadsheet...")
        # Format header
        worksheet.format("A1:Z1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })
        
        # Freeze header
        sheet.batch_update({
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": worksheet.id,
                            "gridProperties": {"frozenRowCount": 1}
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                }
            ]
        })
        
        print("Upload and formatting complete!")
    except Exception as e:
        if "insufficient authentication scopes" in str(e).lower() or isinstance(e, gspread.exceptions.APIError):
            print("\n" + "="*60)
            print("ERROR: Insufficient Google Authentication Scopes.")
            print("Your current application default credentials do not have permission to edit Google Sheets.")
            print("To fix this, please re-authenticate your environment with the proper scopes by running:")
            print("    gcloud auth application-default login --scopes=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive")
            print("After authenticating, re-run this script: python upload_to_sheets.py")
            print("="*60 + "\n")
        else:
            print(f"An unexpected error occurred during upload: {e}")

if __name__ == "__main__":
    upload_to_google_sheets()
