import gspread
from google.oauth2.credentials import Credentials
import os
import csv

SPREADSHEET_ID = "1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY"
TOKEN_PATH = "token.json"

def export_tabs():
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
    
    tabs_to_export = ["Idea Library", "Offer Details", "Opportunities", "Buyer Search"]
    
    for tab in tabs_to_export:
        try:
            ws = sheet.worksheet(tab)
            data = ws.get_all_values()
            filename = f"scratch/{tab.replace(' ', '_')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
            print(f"Exported {tab} to {filename}")
        except Exception as e:
            print(f"Failed to export {tab}: {e}")

if __name__ == "__main__":
    export_tabs()
