import logging
import sqlite3
from datetime import datetime

log = logging.getLogger(__name__)
db_conn = sqlite3.connect('database.db', check_same_thread=False)


class MenuTableConnection:
    def __init__(self, chat_id: int):
        self.__table_name = f'menu_{chat_id}_{datetime.now().isocalendar()[1]}'.replace('-', '')
        self.__order_table_name = f'order_{chat_id}_{datetime.now().strftime("%m/%d/%Y").replace("/", "_")}'.replace('-', '')

    def create(self):
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

    def get_all_menu(self) -> dict[str, dict[int, str]]:
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(
                f'''
                SELECT * FROM {self.__table_name}
                '''
            )
        menu: dict[str, dict[int, str]] = {}
        for weekday_food in cursor.fetchall():
            day, first, second, garnier, salad = weekday_food
            menu[day] = {
                1: first,
                2: second,
                3: garnier,
                4: salad
            }

        return menu
