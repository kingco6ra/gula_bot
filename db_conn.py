import logging
import sqlite3
from datetime import datetime
from sqlite3 import OperationalError
from typing import Any

from telebot.types import InlineKeyboardButton

log = logging.getLogger(__name__)
db_conn = sqlite3.connect('database.db', check_same_thread=False)


class NotifyTableConnection:
    def __init__(self):
        self.__notify_table = f'notify_table'

    def create_notify_table(self) -> bool:
        """
        :return: True - таблица уже существует, False - таблицы не существует и она была создана
        """
        log.info('Creating notify table.')
        with db_conn:
            cursor = db_conn.cursor()
            try:
                cursor.execute(f'''
                create table "{self.__notify_table}"
                    (
                        chat_id integer unique NOT NULL,   
                        enabled bool default True not null,
                        time   str not null,
                        need_clean bool default False not null
                    )
                ''')
            except OperationalError:
                log.error('Table already exists.')
                return True

        log.info('Creating notify table is complete.')
        return False

    def insert_notify_table(self, time: str, chat_id: int):
        log.info('Start insert values.')
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            INSERT INTO {self.__notify_table} VALUES(
            {chat_id}, TRUE, '{time}', FALSE
            )
            ''')
            log.info('Insert values is complete.')
            return True

    def update_notify(self, time: str, chat_id: int):
        log.info('Starting update notify time.')
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            UPDATE {self.__notify_table}
            SET enabled = TRUE, time = '{time}'
            WHERE chat_id = {chat_id}
            ''')
        log.info('Notify time has been updated.')

    def need_clean_table(self, chat_id: int, status: bool):
        log.info('Update "need clean" status on %s', status)
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            UPDATE {self.__notify_table}
            SET need_clean = {status}
            WHERE chat_id = {chat_id}
            ''')

    def get_notifications(self) -> list[dict[str, Any]]:
        with db_conn:
            cursor = db_conn.cursor()
            try:
                cursor.execute(f'SELECT chat_id, enabled, time, need_clean FROM {self.__notify_table}')
            except OperationalError:
                log.error('The table does not exist.')
                self.create_notify_table()
            columns = ('chat_id', 'enabled', 'time', 'need_clean')
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


class MenuTableConnection:
    def __init__(self, chat_id: int):
        self.__table_name = f'menu_{chat_id}_{datetime.now().isocalendar()[1]}'.replace('-', '')
        self.__order_table_name = f'order_{chat_id}_{datetime.now().strftime("%m/%d/%Y").replace("/", "_")}'.replace('-', '')

    def create_week_table(self):
        log.info('Creating new week table.')
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(
                f'''
                    create table "{self.__table_name}"
                        (
                            weekday TEXT not null,
                            soup    TEXT not null,
                            second_course TEXT not null,
                            garnish TEXT not null,
                            salad TEXT not null 
                        )
                ''')
        log.info(f'New table has been created. Table name: {self.__table_name}')

    def insert_menu(self, menu: dict[str, [str, [list[str]]]]):
        log.info('Writing new menu in table.')
        for weekday, food in menu.items():
            soup = '\n'.join(food['soup'])
            second_course = '\n'.join(food['second_course'])
            garnish = '\n'.join(food['garnish'])
            salad = '\n'.join(food['salad'])
            with db_conn:
                cursor = db_conn.cursor()
                cursor.execute(
                    f'''
                INSERT INTO {self.__table_name} VALUES(
                '{weekday}', '{soup}', '{second_course}', '{garnish}', '{salad}'
                )
                ''')
        log.info('New menu has been writed.')

    def get_menu(self, weekday: str) -> list[str] | bool:
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(
                f'''
                SELECT * FROM {self.__table_name}
                WHERE weekday = '{weekday}'
                '''
            )
        menu = []
        try:
            for i in cursor.fetchall()[0][1:]:
                food = ' ИЛИ '.join(i.split(' | ')) + '\n'
                menu.append(food)
        except IndexError:
            log.error('Nothing will be delivered on the weekend.')
            return False
        return menu

    def generate_order_menu(self, day):
        first, second, garnier, salad = self.get_menu(day)
        return {
            'first': [InlineKeyboardButton(dish, callback_data=f'first_0_{index}') for index, dish in enumerate(first.split('\n')[:-1])],
            'second': [InlineKeyboardButton(dish, callback_data=f'second_1_{index}') for index, dish in enumerate(second.split('\n')[:-1])],
            'garnier': [InlineKeyboardButton(dish, callback_data=f'garnier_2_{index}') for index, dish in enumerate(garnier.split('\n')[:-1])],
            'salad': [InlineKeyboardButton(dish, callback_data=f'salad_3_{index}') for index, dish in enumerate(salad.split('\n')[:-1])],
        }

    def create_and_insert_to_order_table(self, user_id: int):
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

    def update_order_table(self, user_id: int, data: str, dish: str):
        log.info('Insert in order table %s: %s', data, dish)
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            UPDATE {self.__order_table_name}
            SET {data} = '{dish}'
            WHERE user_id = {user_id}
            ''')

    def get_from_order_table(self, user_id: int):
        log.info('Getting order from table for user: %s', user_id)
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(f'''
            SELECT * FROM {self.__order_table_name}
            WHERE user_id = {user_id}
            ''')

        return [dish + '\n' for dish in cursor.fetchall()[0][1:]]
