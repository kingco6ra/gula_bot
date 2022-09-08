import logging
from datetime import datetime

from environ_variables import SPREADSHEET_ID
from google_api.init_sheet import get_service

spreadsheets = get_service()
RANGES_FOR_NAME_COLUMN = 'A1:A50'
FULL_WEEK = 'B2:F100'

log = logging.getLogger(__name__)


def get_rows(ranges):
    log.info(f'GET rows from {ranges} range.')
    return spreadsheets.values().get(spreadsheetId=SPREADSHEET_ID,
                                     range=ranges).execute()


def get_weekday(weekday: str | None):
    if weekday:
        return {
            'ПНД': 'B',
            'ВТ': 'C',
            'СР': 'D',
            'ЧТВ': 'E',
            'ПТН': 'F'
        }.get(weekday, None)

    return {
        1: 'B',
        2: 'C',
        3: 'D',
        4: 'E',
        5: 'F'
    }.get(datetime.now().isoweekday())


def write_in_table(body):
    log.info('writing in table')
    spreadsheets.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    log.info('writing complete')
    return


def make_order(name: str, order: list) -> tuple[bool, list[str]]:
    log.info('start ordering')
    sheet_values = get_rows(RANGES_FOR_NAME_COLUMN)['values']
    msg = []
    order_dict = {}
    for line in order:
        day, food_list = line.split(':')
        index_day = get_weekday(day.upper())
        if index_day is None:
            msg.append(f'Заказ не был совершен. Убедитесь что аббревиатура дня недели была заполнена верно. Вы ввели: {day}')
            return False, msg
        order_dict[index_day] = food_list

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

    for day, food_list in order_dict.items():
        food_list = food_list.replace(', ', '\n').lstrip(' ')
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{day}{row_id}",
                    "majorDimension": "ROWS",
                    "values": [[food_list]],
                }
            ]
        }
        write_in_table(body)
        log.info(f'order has been created ({food_list})')
    return True, msg


def clean_orders() -> None:
    write_in_table(body={
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
    })

    body = {
        "requests": [
            {
                "updateCells": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 1,
                        "endRowIndex": len(get_rows(RANGES_FOR_NAME_COLUMN)),
                        "startColumnIndex": 1,
                        "endColumnIndex": 6
                    },
                    "rows": [
                        {
                            "values": [
                                {
                                    "userEnteredFormat": {
                                        "backgroundColor": {
                                            "red": 1,
                                            "green": 1,
                                            "blue": 1,
                                        }
                                    }
                                }
                            ]
                        }
                    ],
                    "fields": "userEnteredFormat.backgroundColor"
                }
            }
        ]

    }
    spreadsheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()


def everyone_paid():
    # TODO: красить только заполненные клетки
    weekday = datetime.now().isoweekday()
    body = {
        "requests": [
            {
                "updateCells": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 1,
                        "endRowIndex": len(get_rows(RANGES_FOR_NAME_COLUMN)['values']),
                        "startColumnIndex": weekday,
                        "endColumnIndex": weekday + 1
                    },
                    "rows": [
                        [{
                            "values": [
                                {
                                    "userEnteredFormat": {
                                        "backgroundColor": {
                                            "green": 0.6,
                                        }
                                    }
                                }
                            ]
                        }] for _ in range(len(get_rows(RANGES_FOR_NAME_COLUMN)['values']) - 1)
                    ],
                    "fields": "userEnteredFormat.backgroundColor"
                }
            }
        ]

    }
    spreadsheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

