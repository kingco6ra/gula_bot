import logging as log

from db_conn import MenuTableConnection, NotifyTableConnection
from google_api.work_with_sheet import get_rows, get_weekday, RANGES_FOR_NAME_COLUMN, write_in_table


class Order:
    def __init__(self, chat_id: int, user_id: int, full_name: str):
        self.__user_id = user_id
        self.__chat_id = chat_id
        self.__full_name = full_name

    def make_order(self):
        log.info('Start writing order in table')
        try:
            sheet_values = get_rows(RANGES_FOR_NAME_COLUMN)['values']
        except Exception:
            sheet_values = []
        name = f'{self.__full_name}\n{self.__user_id}'
        msg = ''
        order = MenuTableConnection(self.__chat_id).get_from_order_table(self.__user_id)

        # Получаем ID пользователя из таблицы. Если такого не существует - добавляем в самый конец.
        try:
            # Под индексом 1 - пустая строка. Поэтому добавляем 1 к получившемуся результату.
            row_id = sheet_values.index([name]) + 1
            log.info('User already exists')
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
            log.info('New user was been created.')
            msg = f'Добавлен новый пользователь: <b>{self.__full_name}</b>'

        sheet_values = get_rows(RANGES_FOR_NAME_COLUMN)['values']
        row_id = sheet_values.index([name]) + 1
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
        write_in_table(body)
        log.info(f'Order has been created for %s has been created.', self.__full_name)
        NotifyTableConnection().need_clean_table(self.__chat_id, True)
        return order, msg
