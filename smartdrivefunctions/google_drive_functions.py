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