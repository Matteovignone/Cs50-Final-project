import os
from google.auth.transport.requests import Request
from google.auth.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
token_file = "token.json"
client_id = "1046891552643-0ran9o91t1vl7c05g68l3o89ecepfqlg.apps.googleusercontent.com"
client_secret = "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"

def authenticate():
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
        {   
            "web": {
            "client_id": "client_id",
            "client_secret": "client_secret",
            "redirect_uris": ["https://www.example.com/login/oauth2callback"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
        }
         },
     SCOPES,        
)
            
    creds = flow.run_local_server(port=5000)
