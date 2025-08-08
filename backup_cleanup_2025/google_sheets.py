import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.sheet_name = os.getenv('SHEET_NAME', 'Articles')
        self.service = self._authenticate()
    
    def _authenticate(self):
        try:
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                credentials_info = json.loads(credentials_json)
            else:
                credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
                with open(credentials_path, 'r') as f:
                    credentials_info = json.load(f)
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {str(e)}")
            raise Exception(f"Google Sheets authentication failed: {str(e)}")
    
    def initialize_sheet(self):
        try:
            headers = [
                'Saved Date', 'Title', 'Author', 'URL', 'Category', 
                'Reading Time', 'Description', 'Keywords', 'Publish Date',
                'Status', 'Notes', 'Saved By', 'Read Date', 'Rating'
            ]
            
            range_name = f'{self.sheet_name}!A1:N1'
            body = {'values': [headers]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.2,
                                        'green': 0.5,
                                        'blue': 0.8
                                    },
                                    'textFormat': {
                                        'foregroundColor': {
                                            'red': 1.0,
                                            'green': 1.0,
                                            'blue': 1.0
                                        },
                                        'bold': True
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    },
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': 0,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': 14
                            }
                        }
                    }
                ]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=format_request
            ).execute()
            
            logger.info("Google Sheet initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize sheet: {str(e)}")
            return False
    
    def save_article(self, article_info):
        try:
            values = [[
                article_info.get('saved_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                article_info.get('title', ''),
                article_info.get('author', ''),
                article_info.get('url', ''),
                article_info.get('category', 'General'),
                article_info.get('reading_time', ''),
                article_info.get('description', ''),
                article_info.get('keywords', ''),
                article_info.get('publish_date', ''),
                article_info.get('status', 'Unread'),
                article_info.get('notes', ''),
                article_info.get('saved_by', ''),
                '',
                ''
            ]]
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:A'
            ).execute()
            
            current_rows = len(result.get('values', [])) if 'values' in result else 0
            next_row = current_rows + 1
            
            range_name = f'{self.sheet_name}!A{next_row}:N{next_row}'
            body = {'values': values}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self._apply_row_formatting(next_row)
            
            logger.info(f"Article saved to row {next_row}")
            return next_row
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.info("Sheet not found, initializing...")
                self.initialize_sheet()
                return self.save_article(article_info)
            else:
                logger.error(f"Failed to save article: {str(e)}")
                raise Exception(f"Failed to save to Google Sheets: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to save article: {str(e)}")
            raise Exception(f"Failed to save article: {str(e)}")
    
    def _apply_row_formatting(self, row_number):
        try:
            category_colors = {
                'AI/Tech': {'red': 0.6, 'green': 0.8, 'blue': 1.0},
                'Programming': {'red': 0.8, 'green': 0.6, 'blue': 1.0},
                'Business': {'red': 1.0, 'green': 0.8, 'blue': 0.6},
                'Design': {'red': 1.0, 'green': 0.6, 'blue': 0.8},
                'Science': {'red': 0.6, 'green': 1.0, 'blue': 0.8},
                'Health': {'red': 0.8, 'green': 1.0, 'blue': 0.6},
                'Education': {'red': 0.7, 'green': 0.9, 'blue': 0.9},
                'General': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            }
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!E{row_number}'
            ).execute()
            
            category = result.get('values', [['']])[0][0] if 'values' in result else 'General'
            color = category_colors.get(category, category_colors['General'])
            
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': row_number - 1,
                                'endRowIndex': row_number,
                                'startColumnIndex': 4,
                                'endColumnIndex': 5
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': color
                                }
                            },
                            'fields': 'userEnteredFormat.backgroundColor'
                        }
                    }
                ]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=format_request
            ).execute()
            
        except Exception as e:
            logger.warning(f"Could not apply formatting: {str(e)}")
    
    def get_recent_articles(self, limit=5):
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A2:N'
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                return []
            
            articles = []
            for row in rows[-limit:]:
                if len(row) >= 7:
                    articles.append({
                        'title': row[1] if len(row) > 1 else '',
                        'url': row[3] if len(row) > 3 else '',
                        'category': row[4] if len(row) > 4 else '',
                        'reading_time': row[5] if len(row) > 5 else '',
                        'status': row[9] if len(row) > 9 else 'Unread'
                    })
            
            return articles[::-1]
            
        except Exception as e:
            logger.error(f"Failed to get recent articles: {str(e)}")
            return []
    
    def get_statistics(self):
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A2:N'
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                return {
                    'total': 0,
                    'read': 0,
                    'unread': 0,
                    'top_category': 'N/A',
                    'total_time': 0
                }
            
            total = len(rows)
            read = sum(1 for row in rows if len(row) > 9 and row[9].lower() == 'read')
            unread = total - read
            
            categories = {}
            total_time = 0
            
            for row in rows:
                if len(row) > 4 and row[4]:
                    category = row[4]
                    categories[category] = categories.get(category, 0) + 1
                
                if len(row) > 5 and row[5]:
                    time_match = re.search(r'(\d+)', row[5])
                    if time_match:
                        total_time += int(time_match.group(1))
            
            top_category = max(categories, key=categories.get) if categories else 'N/A'
            
            return {
                'total': total,
                'read': read,
                'unread': unread,
                'top_category': top_category,
                'total_time': total_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                'total': 0,
                'read': 0,
                'unread': 0,
                'top_category': 'N/A',
                'total_time': 0
            }
    
    def update_article_status(self, row_number, status='Read'):
        try:
            range_name = f'{self.sheet_name}!J{row_number}'
            body = {'values': [[status]]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            if status == 'Read':
                read_date_range = f'{self.sheet_name}!M{row_number}'
                read_date_body = {'values': [[datetime.now().strftime('%Y-%m-%d')]]}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=read_date_range,
                    valueInputOption='RAW',
                    body=read_date_body
                ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update status: {str(e)}")
            return False
    
    def add_note(self, row_number, note):
        try:
            range_name = f'{self.sheet_name}!K{row_number}'
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            current_note = result.get('values', [['']])[0][0] if 'values' in result else ''
            
            if current_note:
                new_note = f"{current_note}\n{note}"
            else:
                new_note = note
            
            body = {'values': [[new_note]]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add note: {str(e)}")
            return False