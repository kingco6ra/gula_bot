import os
from datetime import datetime

from environ_variables import SPREADSHEET_ID
from init_sheet import get_service

SERVICE = get_service()
RANGES_FOR_NAME_COLUMN = 'A1:A50'
FULL_WEEK = 'B2:F100'


def get_all_rows_with_names(ranges):
    return SERVICE.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                               range=ranges).execute()


def write_in_sheet(name: str, order: str) -> bool:
    sheet_values = get_all_rows_with_names(RANGES_FOR_NAME_COLUMN)['values']
    weekday = {
        1: 'B',
        2: 'C',
        3: 'D',
        4: 'E',
        5: 'F'
    }.get(datetime.now().isoweekday())

    try:
        # Под индексом 1 - пустая строка. Поэтому добавляем 1 к получившемуся результату.
        row_id = sheet_values.index([name]) + 1
    except ValueError:
        return False

    SERVICE.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={
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


def clean_orders() -> None:
    service = get_service()
    service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"{FULL_WEEK}",
                'majorDimension': 'ROWS',
                "values": [
                    ['' for _ in range(5)] for _ in range(len(get_all_rows_with_names(RANGES_FOR_NAME_COLUMN)['values']))
                ],
            }
        ]
    }).execute()
