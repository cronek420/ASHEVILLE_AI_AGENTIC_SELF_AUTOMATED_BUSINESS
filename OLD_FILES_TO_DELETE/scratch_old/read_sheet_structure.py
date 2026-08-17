import gspread
from google.oauth2.credentials import Credentials
import os

SPREADSHEET_ID = "1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY"
TOKEN_PATH = "token.json"

def read_structure():
    if not os.path.exists(TOKEN_PATH):
        print("token.json not found!")
        return

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SPREADSHEET_ID)
    print(f"Sheet Title: {sheet.title}")
    
    for ws in sheet.worksheets():
        print(f"\n--- Worksheet: {ws.title} ---")
        try:
            headers = ws.row_values(1)
            print(f"Headers: {headers}")
            
            # Read row 2 to see example data
            data = ws.row_values(2)
            if data:
                print(f"Row 2 (Example): {data}")
        except Exception as e:
            print(f"Could not read row 1: {e}")

if __name__ == "__main__":
    read_structure()
