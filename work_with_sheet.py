import os
from datetime import datetime

from environ_variables import SPREADSHEET_ID
from init_sheet import get_service


def write_in_sheet(name: str, order: str):
    service = get_service()
    weekday = {
        1: 'B',
        2: 'C',
        3: 'D',
        4: 'E',
        5: 'F'
    }.get(datetime.now().isoweekday())
    ranges = 'A1:A50'
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                 range=ranges).execute()

    sheet_values: list[list] = result['values']
    try:
        # Под индексом 1 - пустая строка. Поэтому добавляем 1 к получившемуся результату.
        row_id = sheet_values.index([name]) + 1
    except ValueError:
        return False

    service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={
        "valueInputOption": "USER_ENTERED",  # Данные воспринимаются, как вводимые пользователем (считается значение формул)
        "data": [
            {
                "range": f"{weekday}{row_id}",
                "majorDimension": "ROWS",
                "values": [[order]],
            }
        ]
    }).execute()
    return True


def clean_week():
    full_week = 'B2:F113'
    service = get_service()
    return service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"{full_week}",
                "majorDimension": "ROWS",
                "values": [['']],
            }
        ]
    }).execute()
