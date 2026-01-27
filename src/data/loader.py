import pandas as pd
from typing import List, Union
from pathlib import Path
from src.models.schemas import LeadInput
from src.utils.validators import validate_lead_data


class DataLoader:
    """Load lead data from CSV or Google Sheets"""
    
    @staticmethod
    def load_from_csv(file_path: Union[str, Path]) -> List[LeadInput]:
        """
        Load leads from CSV file
        
        Expected columns:
        - business_name
        - category
        - city
        - state
        - website_url (optional)
        - email (optional)
        """
        df = pd.read_csv(file_path)
        
        # Fill NaN values for optional fields
        df['website_url'] = df['website_url'].fillna('')
        df['email'] = df['email'].fillna('')
        
        leads = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                lead = validate_lead_data(row.to_dict())
                leads.append(lead)
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        if errors:
            print(f"⚠️  Validation errors found:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")
        
        print(f"✓ Loaded {len(leads)} valid leads from CSV")
        return leads
    
    @staticmethod
    def load_from_google_sheets(sheet_id: str, credentials_path: str) -> List[LeadInput]:
        """
        Load leads from Google Sheets
        
        Requires:
        - Google Sheets API enabled
        - Service account credentials
        """
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError("Google Sheets support requires: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        
        # Authenticate
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Read data
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='A:F'  # Adjust range as needed
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            raise ValueError("No data found in sheet")
        
        # First row is headers
        headers = values[0]
        rows = values[1:]
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=headers)
        df['website_url'] = df.get('website_url', pd.Series(dtype=str)).fillna('')
        df['email'] = df.get('email', pd.Series(dtype=str)).fillna('')
        
        leads = []
        for idx, row in df.iterrows():
            try:
                lead = validate_lead_data(row.to_dict())
                leads.append(lead)
            except Exception as e:
                print(f"⚠️  Row {idx}: {str(e)}")
        
        print(f"✓ Loaded {len(leads)} valid leads from Google Sheets")
        return leads