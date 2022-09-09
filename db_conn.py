import logging
import sqlite3
from datetime import datetime
from sqlite3 import OperationalError

log = logging.getLogger(__name__)


class DataBaseConnection:
    def __init__(self, chat_id):
        self.__menu_table = f'menu_{chat_id}_{datetime.now().isocalendar()[1]}'.replace('-', '')
        self.__notify_table = f'notify_{chat_id}'.replace('-', '')
        self.connect = sqlite3.connect('database.db', check_same_thread=False)

    def create_notify_table(self, time: str) -> bool:
        log.info('Creating notify table.')
        with self.connect:
            cursor = self.connect.cursor()
            try:
                cursor.execute(f'''
                create table "{self.__notify_table}"
                    (
                        status bool default FALSE not null,
                        time   str default '{time}' not null
                    )
                ''')
                log.info('Creating notify table is complete.')
            except OperationalError:
                log.error('Table already exists.')
                return False

            log.info('Start insert values.')
            cursor.execute(f'''
            INSERT INTO {self.__notify_table} VALUES(
            TRUE, '{time}'
            )
            ''')
            log.info('Insert values is complete.')
            return True

    def change_notify(self, time: str):
        log.info('Starting change notify time.')
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(f'''
            UPDATE {self.__notify_table}
            SET time = '{time}'
            ''')
        log.info('Notify time has been changed.')

    def get_notify(self):# -> dict[str[bool], str[str]]:
        log.info('Getting notify status.')
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(f'SELECT status, time FROM {self.__notify_table}')
            return cursor.fetchall()

    def create_week_table(self):
        log.info('Creating new week table.')
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(
                f'''
                    create table "{self.__menu_table}"
                        (
                            weekday TEXT not null,
                            soup    TEXT not null,
                            second_course TEXT not null,
                            garnish TEXT not null,
                            salad TEXT not null 
                        )
                ''')
        log.info(f'New table has been created. Table name: {self.__menu_table}')

    def insert_menu(self, menu: dict[str, [str, [list[str]]]]):
        log.info('Writing new menu in table.')
        for weekday, food in menu.items():
            soup = '\n'.join(food['soup'])
            second_course = '\n'.join(food['second_course'])
            garnish = '\n'.join(food['garnish'])
            salad = '\n'.join(food['salad'])
            with self.connect:
                cursor = self.connect.cursor()
                cursor.execute(
                    f'''
                INSERT INTO {self.__menu_table} VALUES(
                '{weekday}', '{soup}', '{second_course}', '{garnish}', '{salad}'
                )
                ''')
        log.info('New menu has been writed.')

    def get_menu(self, weekday: str):
        with self.connect:
            cursor = self.connect.cursor()
            cursor.execute(
                f'''
                SELECT * FROM {self.__menu_table}
                WHERE weekday = '{weekday}'
                '''
            )
        menu = []
        for i in cursor.fetchall()[0][1:]:
            food = ' ИЛИ '.join(i.split(' | ')) + '\n'
            menu.append(food)
        return menu
