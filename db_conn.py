import logging
import sqlite3
from datetime import datetime
from sqlite3 import OperationalError

log = logging.getLogger(__name__)
connect = sqlite3.connect('database.db', check_same_thread=False)
DAY_MONTH = f'menu_{datetime.now().isocalendar()[1]}'


def create_week_table():
    log.info('creating week table')
    with connect:
        cursor = connect.cursor()
        cursor.execute(
            f'''
                create table "{DAY_MONTH}"
                    (
                        weekday TEXT not null,
                        menu    TEXT not null
                    )
            ''')


def insert_menu(menu: dict[str, list[str]]):
    log.info('insert new menu')
    for weekday, line in menu.items():
        line = ' | '.join(line)
        with connect:
            cursor = connect.cursor()
            cursor.execute(
                f'''
            INSERT INTO {DAY_MONTH} VALUES('{weekday}', '{line}')'''
            )
    log.info('new menu has been writed')


def get_menu(weekday):
    with connect:
        cursor = connect.cursor()
        cursor.execute(
            f'''
            SELECT weekday, menu FROM {DAY_MONTH}
            WHERE weekday = '{weekday}'
            '''
        )

    menu = cursor.fetchall()[0][1]
    return menu.rstrip()