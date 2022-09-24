import logging as log

from database import OrderTableConnection, NotifyTableConnection
from google_api.work_with_sheet import get_weekday, GoogleSheets


class ButtonOrder:
    def __init__(self, chat_id: int, user_id: int, full_name: str):
        self.__user_id = user_id
        self.__chat_id = chat_id
        self.__full_name = full_name
        self.__name = f'{self.__full_name}\n{self.__user_id}'
        self.__google_sheets = GoogleSheets()

        try:
            self.__sheet_values: list[list[str]] = self.__google_sheets.get_rows()['values']
        except Exception:
            self.__sheet_values: list[list[str]] = [[]]

    def get_row_id(self) -> tuple[int, str]:
        """Получаем номер строки пользователя из таблицы. Если такого не существует - добавляем в самый конец."""
        try:
            row_id = None
            for value in self.__sheet_values:
                for name in value:
                    if str(self.__user_id) in name:
                        row_id = self.__sheet_values.index([name]) + 1

            assert row_id is not None
            log.info('User already exists.')
            return row_id, ''

        except AssertionError:
            # Получаем ID первой свободной строки и добавляем туда новое имя.
            log.info('User not exists. Creating...')
            last_row_id = len(self.__sheet_values) + 1
            body = {  # TODO: запилить оформление при создании, а пока что ручками
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"A{last_row_id}:A{last_row_id}",
                        "majorDimension": "ROWS",
                        "values": [[self.__name]],
                    },
                ]
            }
            self.__google_sheets.write(body)
            log.info('New user was been created.')
            return last_row_id, 'Создан новый пользователь.'

    def make_order(self):
        log.info('Start writing order in table')
        order = OrderTableConnection(self.__chat_id).get_all(self.__user_id)
        row_id, msg = self.get_row_id()
        day = get_weekday()
        order = ''.join(order)
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{day}{row_id}",
                    "majorDimension": "ROWS",
                    "values": [[order]],
                }
            ]
        }
        self.__google_sheets.write(body)
        log.info(f'Order has been created for %s has been created.', self.__full_name)
        NotifyTableConnection().need_clean_table(self.__chat_id, True)
        return order, msg
