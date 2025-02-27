import os
import json
import datetime
from typing import Dict, List, Optional, Union
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import dateutil.parser

# Define the scopes (permissions) required for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    """Service for interacting with Google Calendar API.
    
    This class handles authentication and event creation for Google Calendar.
    """
    
    def __init__(self, credentials_path: str = 'credentials.json', 
                 token_path: str = 'token.json'):
        """Initialize the Google Calendar service.
        
        Args:
            credentials_path: Path to the credentials JSON file from Google Cloud
            token_path: Path where the user's access tokens will be saved
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials = self._get_credentials()
        
        if self.credentials:
            self.service = build('calendar', 'v3', credentials=self.credentials)
        else:
            self.service = None
            print("Warning: Google Calendar service could not be initialized.")
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get valid user credentials.
        
        This function handles the OAuth2 flow to get user credentials for
        accessing Google Calendar. It will attempt to load cached credentials
        or initiate a new OAuth flow if needed.
        
        Returns:
            Credentials object or None if authorization fails
        """
        creds = None
        
        # Check if token.json exists with cached credentials
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(open(self.token_path).read()),
                    SCOPES
                )
            except Exception as e:
                print(f"Error loading cached credentials: {e}")
        
        # If no valid credentials available, authenticate user
        if not creds or not creds.valid:
            # Try to refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            # Get new credentials if refresh failed or no credentials exist
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error in authentication flow: {e}")
                    return None
                
            # Save the credentials for future runs
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def is_authenticated(self) -> bool:
        """Check if the service is authenticated and ready to use.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.service is not None
    
    def add_event(self, event_data: Dict) -> Optional[Dict]:
        """Add an event to Google Calendar.
        
        Args:
            event_data: Dictionary with event details
            
        Returns:
            Created event data or None if operation fails
        """
        if not self.is_authenticated():
            print("Error: Calendar service not authenticated")
            return None
        
        try:
            # Parse start and end times
            start_datetime = dateutil.parser.parse(event_data['start_datetime'])
            end_datetime = dateutil.parser.parse(event_data['end_datetime'])
            
            # Create Google Calendar event
            event = {
                'summary': event_data['summary'],
                'location': event_data.get('location', ''),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/New_York',  # Default timezone, could be parameterized
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/New_York',  # Default timezone, could be parameterized
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 90},       # 1.5 hours before
                    ],
                },
            }
            
            # Insert the event
            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            return {
                'id': created_event.get('id'),
                'htmlLink': created_event.get('htmlLink'),
                'status': 'created'
            }
        
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

    def list_upcoming_events(self, max_results: int = 10) -> List[Dict]:
        """List upcoming events on the user's calendar.
        
        Args:
            max_results: Maximum number of events to return
            
        Returns:
            List of upcoming events
        """
        if not self.is_authenticated():
            print("Error: Calendar service not authenticated")
            return []
        
        try:
            # Get current time in UTC
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format the events
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'id': event.get('id'),
                    'summary': event.get('summary'),
                    'start': start,
                    'htmlLink': event.get('htmlLink')
                })
                
            return formatted_events
            
        except Exception as e:
            print(f"Error listing calendar events: {e}")
            return []