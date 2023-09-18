from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import pickle
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build
import os
import asyncio

from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)

# Make services to access the contents of google drive
def build_services():
    creds,drive=get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)
    sheet_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return(docs_service,sheet_service,drive_service,drive)



# Get credentials for google drive
def get_credentials():
    # path to credentials
    secret_path="../client_secret_530730093415-kv2qvv04b3r6evnfevvpmbupmkpauarr.apps.googleusercontent.com.json"
    gauth_token_path="../gauth_token.pickle"
    pydrive_token_path="../token.pickle"

    # gauth setup
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(secret_path)
    if not os.path.exists(gauth_token_path):
        gauth.LocalWebserverAuth()
        with open(gauth_token_path, "wb") as f:
            pickle.dump(gauth.credentials, f)
    else:
        with open(gauth_token_path, "rb") as f:
            gauth.credentials = pickle.load(f)
    drive = GoogleDrive(gauth)

    # pydrive and credential setup
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/documents.readonly']
    creds = None
    if os.path.exists(pydrive_token_path):
        with open(pydrive_token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds,drive


# Get information from google sheets
async def get_from_sheets(creds, sheet_id):
    sheet_service = build('sheets', 'v4', credentials=creds)
    # Use the run_in_executor method to run the fetch_doc_content function
    content = await asyncio.get_event_loop().run_in_executor(executor, fetch_sheet_content, sheet_service, sheet_id)
    return content
def fetch_sheet_content(sheet_service,sheet_id):
    content="This is a spreadsheet:\n"
    try:
        result = sheet_service.spreadsheets().values().get(spreadsheetId=sheet_id, range="Log!A1:Z100").execute()
        values = result.get('values', [])
        for i in range(len(values)):
            for j in range(len(values[i])):
                content+=values[i][j]+" "
            content+="\n"
    except HttpError as err:
        print(err)
    return(content)


async def get_from_docs(creds, doc_id):
    docs_service = build('docs', 'v1', credentials=creds)
    # Use the run_in_executor method to run the fetch_doc_content function
    content = await asyncio.get_event_loop().run_in_executor(executor, fetch_doc_content, docs_service, doc_id)
    return content
def fetch_doc_content(docs_service, doc_id):
    content = ""
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        for piece in doc['body']["content"]:
            if 'paragraph' in piece.keys() and 'textRun' in piece['paragraph']['elements'][0].keys():
                content += piece["paragraph"]["elements"][0]['textRun']['content']
    except HttpError as err:
        print(err)
    return content