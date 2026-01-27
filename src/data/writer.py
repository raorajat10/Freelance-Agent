import json
import pandas as pd
from typing import List
from pathlib import Path
from src.models.schemas import LeadOutput


class DataWriter:
    """Write qualified lead results to output formats"""
    
    @staticmethod
    def write_to_json(results: List[LeadOutput], output_path: str):
        """Write results to JSON file"""
        data = [result.model_dump() for result in results]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Results written to {output_path}")
    
    @staticmethod
    def write_to_csv(results: List[LeadOutput], output_path: str):
        """Write results to CSV file"""
        data = [result.model_dump() for result in results]
        df = pd.DataFrame(data)
        
        # Convert list fields to strings for CSV
        df['website_issues'] = df['website_issues'].apply(lambda x: '; '.join(x) if x else '')
        
        df.to_csv(output_path, index=False)
        print(f"✓ Results written to {output_path}")
    
    @staticmethod
    def write_to_google_sheets(results: List[LeadOutput], sheet_id: str, credentials_path: str):
        """Write results to Google Sheets"""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Google Sheets support requires: "
                "pip install google-auth google-auth-oauthlib "
                "google-auth-httplib2 google-api-python-client"
            )
        
        # Authenticate
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Prepare data
        headers = [
            'business_name',
            'website_status',
            'website_issues',
            'lead_score',
            'priority',
            'outreach_message'
        ]
        values = [headers]
        
        for result in results:
            row = [
                result.business_name,
                result.website_status,
                '; '.join(result.website_issues) if result.website_issues else '',
                result.lead_score,
                result.priority,
                result.outreach_message
            ]
            values.append(row)
        
        # Write to sheet (creates or overwrites 'Results' tab)
        body = {'values': values}
        
        try:
            # Try to update existing sheet
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='Results!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
        except Exception as e:
            # If 'Results' sheet doesn't exist, create it first
            try:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={
                        'requests': [{
                            'addSheet': {
                                'properties': {
                                    'title': 'Results'
                                }
                            }
                        }]
                    }
                ).execute()
                
                # Now write data
                service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range='Results!A1',
                    valueInputOption='RAW',
                    body=body
                ).execute()
            except Exception as create_error:
                raise Exception(f"Failed to write to Google Sheets: {str(create_error)}")
        
        print(f"✓ Results written to Google Sheets (sheet ID: {sheet_id})")