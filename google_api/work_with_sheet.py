import logging
from datetime import datetime

from environ_variables import SPREADSHEET_ID
from google_api.init_sheet import get_service

SERVICE = get_service()
RANGES_FOR_NAME_COLUMN = 'A1:A50'
FULL_WEEK = 'B2:F100'

log = logging.getLogger(__name__)


def get_rows(ranges):
    log.info(f'GET rows from {ranges} range.')
    return SERVICE.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                               range=ranges).execute()


def write_in_table(body):
    log.info('writing in table')
    SERVICE.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    log.info('writing complete')
    return


def make_order(name: str, order: str) -> tuple[bool, list[str]]:
    log.info('start ordering')
    # TODO: добавить возможность делать заказы на определенные дни недели
    sheet_values = get_rows(RANGES_FOR_NAME_COLUMN)['values']
    weekday = {
        1: 'B',
        2: 'C',
        3: 'D',
        4: 'E',
        5: 'F'
    }.get(datetime.now().isoweekday())
    msg = []

    # Получаем ID пользователя из таблицы. Если такого не существует - добавляем в самый конец.
    try:
        # Под индексом 1 - пустая строка. Поэтому добавляем 1 к получившемуся результату.
        row_id = sheet_values.index([name]) + 1
        log.info('user already exists')
    except ValueError:
        # Получаем ID первой свободной строки и добавляем туда новое имя.
        log.info('user not exists. creating...')
        last_row_id = len(sheet_values) + 1
        body = {  # TODO: запилить оформление при создании, а пока что ручками
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"A{last_row_id}:A{last_row_id}",
                    "majorDimension": "ROWS",
                    "values": [[name]],
                },
            ]
        }
        write_in_table(body)
        msg.append(
            f'Добавлен новый пользователь: {name}'
        )
        sheet_values = get_rows(RANGES_FOR_NAME_COLUMN)['values']
        row_id = sheet_values.index([name]) + 1
        log.info('new user was been created.')

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"{weekday}{row_id}",
                "majorDimension": "ROWS",
                "values": [[order]],
            }
        ]
    }
    write_in_table(body)
    log.info('order has been created')
    return True, msg


def clean_orders() -> None:
    service = get_service()
    service.spreadsheets().values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"{FULL_WEEK}",
                'majorDimension': 'ROWS',
                "values": [
                    ['' for _ in range(5)] for _ in range(len(get_rows(RANGES_FOR_NAME_COLUMN)['values']))
                ],
            }
        ]
    }).execute()
