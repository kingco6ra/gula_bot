import logging as log
import sqlite3
from sqlite3 import OperationalError

db_conn = sqlite3.connect('database.db', check_same_thread=False)


class NotifyTableConnection:
    def __init__(self):
        self.__notify_table = f'notify_table'

    def create(self) -> bool:
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

    def insert(self, time: str, chat_id: int):
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

    def update(self, time: str, chat_id: int):
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

    def get_notifications(self) -> list[dict[str, any]]:
        with db_conn:
            cursor = db_conn.cursor()
            try:
                cursor.execute(f'SELECT chat_id, enabled, time, need_clean FROM {self.__notify_table}')
            except OperationalError:
                log.error('The table does not exist.')
                self.create()
            columns = ('chat_id', 'enabled', 'time', 'need_clean')
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
