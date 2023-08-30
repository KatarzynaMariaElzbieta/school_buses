import gspread as gs
from google.oauth2 import service_account

from const_config import SERVICE

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = service_account.Credentials.from_service_account_file(SERVICE, scopes=SCOPES)
client = gs.authorize(credentials)


