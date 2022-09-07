import logging
import sqlite3

log = logging.getLogger(__name__)
connect = sqlite3.connect('database.db', check_same_thread=False)


def create_week_table(table_name: str):
    log.info('Creating new week table.')
    with connect:
        cursor = connect.cursor()
        cursor.execute(
            f'''
                create table "{table_name}"
                    (
                        weekday TEXT not null,
                        soup    TEXT not null,
                        second_course TEXT not null,
                        salad TEXT not null 
                    )
            ''')
    log.info('New table has been created. Table name:')


def insert_menu(menu: dict[str, [str, [list[str]]]], table_name: str):
    log.info('Writing new menu in table.')
    for weekday, food in menu.items():
        soup = ', '.join(food['soup'])
        second_course = ', '.join(food['second_course'])
        salad = ', '.join(food['salad'])
        with connect:
            cursor = connect.cursor()
            cursor.execute(
                f'''
            INSERT INTO {table_name} VALUES(
            '{weekday}', '{soup}', '{second_course}', '{salad}'
            ''')
    log.info('New menu has been writed.')


def get_menu(weekday: str, table_name: str):
    with connect:
        cursor = connect.cursor()
        cursor.execute(
            f'''
            SELECT * FROM {table_name}
            WHERE weekday = '{weekday}'
            '''
        )

    menu = []
    for item in cursor.fetchall()[0][1].split(' | '):
        item = item.split(' или ')
        print(item)
        if '' not in item:
            menu.append(item)
    return menu


print(get_menu('ВТ'))
