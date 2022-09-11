import logging
import sqlite3
from datetime import datetime
from sqlite3 import OperationalError

log = logging.getLogger(__name__)


class DataBaseConnection:
    def __init__(self):
        self.__notify_table = f'notify_table'
        self.connect = sqlite3.connect('database.db', check_same_thread=False)

    def create_notify_table(self) -> bool:
        """

        :return: True - таблица уже существует, False - таблицы не существует и она была создана
        """
        log.info('Creating notify table.')
        with self.connect:
            cursor = self.connect.cursor()
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
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(f'''
            INSERT INTO {self.__notify_table} VALUES(
            {chat_id}, TRUE, '{time}', FALSE
            )
            ''')
            log.info('Insert values is complete.')
            return True

    def update_notify(self, time: str, chat_id: int):
        log.info('Starting update notify time.')
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(f'''
            UPDATE {self.__notify_table}
            SET enabled = TRUE, time = '{time}'
            WHERE chat_id = {chat_id}
            ''')
        log.info('Notify time has been updated.')

    def need_clean_table(self, chat_id: int, status: bool):
        log.info('Update "need clean" status on %s', status)
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(f'''
            UPDATE {self.__notify_table}
            SET need_clean = {status}
            WHERE chat_id = {chat_id}
            ''')

    def get_notifications(self):  # -> dict[str[bool], str[str]]:
        with self.connect:
            cursor = self.connect.cursor()
            try:
                cursor.execute(f'SELECT chat_id, enabled, time, need_clean FROM {self.__notify_table}')
            except OperationalError:
                log.error('The table does not exist.')
                self.create_notify_table()
            columns = ('chat_id', 'enabled', 'time', 'need_clean')
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_week_table(self, chat_id: int):
        menu_table = f'menu_{chat_id}_{datetime.now().isocalendar()[1]}'.replace('-', '')
        log.info('Creating new week table.')
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(
                f'''
                    create table "{menu_table}"
                        (
                            weekday TEXT not null,
                            soup    TEXT not null,
                            second_course TEXT not null,
                            garnish TEXT not null,
                            salad TEXT not null 
                        )
                ''')
        log.info(f'New table has been created. Table name: {menu_table}')

    def insert_menu(self, menu: dict[str, [str, [list[str]]]], chat_id: int):
        log.info('Writing new menu in table.')
        menu_table = f'menu_{chat_id}_{datetime.now().isocalendar()[1]}'.replace('-', '')
        for weekday, food in menu.items():
            soup = '\n'.join(food['soup'])
            second_course = '\n'.join(food['second_course'])
            garnish = '\n'.join(food['garnish'])
            salad = '\n'.join(food['salad'])
            with self.connect:
                cursor = self.connect.cursor()
                cursor.execute(
                    f'''
                INSERT INTO {menu_table} VALUES(
                '{weekday}', '{soup}', '{second_course}', '{garnish}', '{salad}'
                )
                ''')
        log.info('New menu has been writed.')

    def get_menu(self, weekday: str, chat_id: int) -> list[str] | bool:
        menu_table = f'menu_{chat_id}_{datetime.now().isocalendar()[1]}'.replace('-', '')
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(
                f'''
                SELECT * FROM {menu_table}
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
