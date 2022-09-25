import logging
from datetime import datetime

from environ_variables import SPREADSHEET_ID
from google_api.init_sheet import get_service

spreadsheets = get_service()
FULL_WEEK = 'B2:F100'

log = logging.getLogger(__name__)


class GoogleSheets:
    def __init__(self):
        self.__spreadsheet_id = SPREADSHEET_ID
        self.__column_ranges = 'A1:A50'
        self.__sheet_values = self.get_rows()

    def write(self, body) -> None:
        log.info('writing in table')
        spreadsheets.values().batchUpdate(spreadsheetId=self.__spreadsheet_id, body=body).execute()
        log.info('writing complete')

    def get_rows(self):
        log.info(f'GET rows from {self.__column_ranges} range.')
        try:
            return spreadsheets.values().get(spreadsheetId=self.__spreadsheet_id,
                                             range=self.__column_ranges).execute()['values']
        except KeyError:
            log.error('Google sheet is empty.')
            return [[]]

    def write_menu(self, menu: dict[str, dict[int, str]]):
        """Записывает недельное меню на второй лист"""
        for day, food in menu.items():
            day = get_weekday(day)
            for row_id, food in food.items():
                body = {
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {
                            "range": f"menu!{day}{row_id}",
                            "majorDimension": "ROWS",
                            "values": [[food]],
                        }
                    ]
                }
                self.write(body)

    def clean_orders(self) -> None:
        self.write(body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{FULL_WEEK}",
                    'majorDimension': 'ROWS',
                    "values": [
                        ['' for _ in range(5)] for _ in range(len(self.get_rows()))
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
                            "endRowIndex": len(self.get_rows()),
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

    def everyone_paid(self) -> None:
        # TODO: красить только заполненные клетки
        weekday = datetime.now().isoweekday()
        body = {
            "requests": [
                {
                    "updateCells": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": 1,
                            "endRowIndex": len(self.get_rows()),
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
                            }] for _ in range(len(self.get_rows()) - 1)
                        ],
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                }
            ]

        }
        spreadsheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

    def make_order(self, name: str, order: list) -> tuple[bool, list[str]]:
        log.info('Start ordering.')
        msg = []
        try:
            row_id = self.__sheet_values.index([name]) + 1
            log.info('User already exists.')
        except ValueError:
            log.info('User not exists. Creating.')
            row_id = len(self.__sheet_values) + 1
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"A{row_id}:A{row_id}",
                        "majorDimension": "ROWS",
                        "values": [[name]],
                    },
                ]
            }
            self.write(body)
            msg.append(
                f'Добавлен новый пользователь: {name}'
            )
            log.info('New user was been created.')

        order_dict = {}
        for line in order:
            day, food_list = line.split(':')
            index_day = get_weekday(day.upper())
            if index_day is None:
                msg.append(f'Заказ не был совершен. Убедитесь что аббревиатура дня недели была заполнена верно. Вы ввели: {day}')
                return False, msg
            order_dict[index_day] = food_list

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
            self.write(body)
            log.info(f'Order has been created.')
        return True, msg


def get_weekday(weekday: str | None = None) -> str:
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
