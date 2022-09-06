import sqlite3
from datetime import datetime

from parse import parse_menu

connect = sqlite3.connect('database.db', check_same_thread=False)
DAY_MONTH = f'menu_{datetime.now().strftime("%d_%m")}'


def create_week_table():
    with connect:
        cursor = connect.cursor()
        cursor.execute(
            f'''create table "{DAY_MONTH}"
                (
                    weekday TEXT not null,
                    menu    TEXT not null
                )
        ''')


def insert_menu(menu: dict[str, list[str]]):
    create_week_table()
    table_name = DAY_MONTH
    for weekday, line in menu.items():
        line = ', '.join(line)
        with connect:
            cursor = connect.cursor()
            cursor.execute(
                f'''
            INSERT INTO {table_name} VALUES('{weekday}', '{line}')'''
            )


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
