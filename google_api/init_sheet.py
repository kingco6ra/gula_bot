import os

import httplib2
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from environ_variables import API_KEY

CREDENTIALS_FILE = f'{os.getcwd()}/google_api/token.json'


def get_service():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                   ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

    httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
    return build('sheets', 'v4', developerKey=API_KEY, http=httpAuth).spreadsheets()


def get_init_table(service):
    spreadsheet = service.spreadsheets().create(body={
        'properties': {'title': 'lunch-table', 'locale': 'ru_RU'},
        'sheets': [{'properties': {'sheetType': 'GRID',
                                   'sheetId': 0,
                                   'title': 'One',
                                   'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
    }).execute()
    spreadsheetId = spreadsheet['spreadsheetId']
    print('https://docs.google.com/spreadsheets/d/' + spreadsheetId)
