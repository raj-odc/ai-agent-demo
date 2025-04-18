import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the scope for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class GoogleSheetsSync:
    def __init__(self):
        # Initialize last sync time
        self.last_sync_time = None
        # Load credentials from service account file
        self.creds_file = os.getenv('GOOGLE_SHEETS_CREDS_FILE')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        
        if not self.spreadsheet_id:
            raise ValueError('Google Sheets spreadsheet ID not found in environment variables')
        
        # Resolve credentials file path relative to project root
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.creds_file)
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f'Credentials file not found at: {creds_path}')
        
        try:
            self.creds = Credentials.from_service_account_file(
                creds_path,
                scopes=SCOPES
            )
        except Exception as e:
            raise ValueError(f'Invalid credentials file format: {str(e)}')

        try:
            print("Attempting to authorize with credentials...")
            self.client = gspread.authorize(self.creds)
            print(f"Authorization successful. Client: {self.client}")
            
            print(f"Attempting to open spreadsheet with ID: {self.spreadsheet_id}")
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print(f"Successfully opened spreadsheet: {spreadsheet.title}")
            
            print("Accessing first sheet...")
            self.sheet = spreadsheet.sheet1
            print(f"Successfully accessed sheet: {self.sheet.title}")
            
            # Verify access by attempting to read cell A1
            try:
                self.sheet.acell('A1')
                print("Successfully verified read access to sheet")
            except Exception as e:
                raise Exception(f"Sheet access verification failed: {str(e)}")
                
        except gspread.exceptions.APIError as e:
            print(f"Google Sheets API Error: {str(e)}")
            if 'PERMISSION_DENIED' in str(e):
                print("This appears to be a permissions issue. Please verify:")
                print("1. The service account email has been shared with the spreadsheet")
                print("2. The service account has edit access to the spreadsheet")
            raise
        except Exception as e:
            print(f"Error during Google Sheets initialization: {str(e)}")
            import traceback
            traceback.print_exc()
            print("Please verify:")
            print("1. Your credentials file is properly formatted")
            print("2. Your spreadsheet ID is correct")
            print("3. Your internet connection is stable")
            raise Exception(f"Failed to initialize Google Sheets connection: {str(e)}")

    
    def sync_to_sheets(self, df):
        """Sync DataFrame to Google Sheets"""
        try:
            # Convert DataFrame to list of lists
            data = [df.columns.values.tolist()] + df.values.tolist()
            
            # Clear existing content and update with new data
            self.sheet.clear()
            self.sheet.update('A1', data)
            
            return True
        except Exception as e:
            print(f'Error syncing to Google Sheets: {str(e)}')
            return False
    
    def sync_from_sheets(self):
        """Sync data from Google Sheets to DataFrame"""
        try:
            # Get the current sheet modification time
            sheet_metadata = self.sheet.spreadsheet.fetch_sheet_metadata()
            current_sync_time = sheet_metadata['properties']['modifiedTime']
            
            # Check if sheet has been modified since last sync
            if self.last_sync_time and current_sync_time <= self.last_sync_time:
                return None
            
            # Update last sync time
            self.last_sync_time = current_sync_time
            
            # Get all values from the sheet
            data = self.sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Convert date strings back to datetime
            if 'Due Date' in df.columns:
                df['Due Date'] = pd.to_datetime(df['Due Date']).dt.strftime('%Y-%m-%d')
            if 'Created Date' in df.columns:
                df['Created Date'] = pd.to_datetime(df['Created Date']).dt.strftime('%Y-%m-%d')
            
            return df
        except Exception as e:
            print(f'Error syncing from Google Sheets: {str(e)}')
            import traceback
            traceback.print_exc()
            return None