import sqlite3
from datetime import datetime
import logging
from telebot.types import InlineKeyboardButton

from database.menu_db import MenuTableConnection

log = logging.getLogger(__name__)
db_conn = sqlite3.connect('database.db', check_same_thread=False)


class OrderTableConnection:
    def __init__(self, chat_id: int):
        self.__order_table_name = f'order_{chat_id}_{datetime.now().strftime("%m/%d/%Y").replace("/", "_")}'.replace('-', '')
        self.__menu_conn = MenuTableConnection(chat_id)

    def create_and_insert(self, user_id: int):
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {self.__order_table_name} (
                    user_id integer unique not null,
                    first TEXT null,
                    second TEXT null,
                    garnier TEXT null,
                    salad TEXT null
                )
                ''')
            try:
                cursor.execute(
                    f'''
                    INSERT INTO {self.__order_table_name} VALUES(
                    {user_id}, null, null, null, null
                    )
                    ''')
                log.info('User has been added to order table.')
            except Exception:
                log.info('User already exists in order table.')

    def update(self, user_id: int, data: str, dish: str):
        log.info('Insert in order table %s: %s', data, dish)
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            UPDATE {self.__order_table_name}
            SET {data} = '{dish}'
            WHERE user_id = {user_id}
            ''')

    def get_user_order(self, user_id: int):
        log.info('Getting order from table for user: %s', user_id)
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            SELECT * FROM {self.__order_table_name}
            WHERE user_id = {user_id}
            ''')

        return [dish + '\n' for dish in cursor.fetchall()[0][1:]]

    def get_all(self):
        log.info('Getting all orders from table.')
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            SELECT * FROM {self.__order_table_name}
            ''')
        return cursor.fetchall()

    # TODO: идеологически правильнее было бы перенести в menu_db
    def get_menu_markup(self, day):
        first, second, garnier, salad = self.__menu_conn.get_menu(day)

        return {
            'first': [InlineKeyboardButton(dish, callback_data=f'first_0_{index}') for index, dish in enumerate(first.split('\n')[:-1])],
            'second': [InlineKeyboardButton(dish, callback_data=f'second_1_{index}') for index, dish in enumerate(second.split('\n')[:-1])],
            'garnier': [InlineKeyboardButton(dish, callback_data=f'garnier_2_{index}') for index, dish in enumerate(garnier.split('\n')[:-1])],
            'salad': [InlineKeyboardButton(dish, callback_data=f'salad_3_{index}') for index, dish in enumerate(salad.split('\n')[:-1])],
        }

    def drop_table(self):
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            DROP TABLE {self.__order_table_name}
            ''')
