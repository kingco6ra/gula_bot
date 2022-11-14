import logging
from datetime import datetime
from sqlite3 import OperationalError

from pandas import read_excel

from database import OrderTableConnection
from collections import defaultdict

log = logging.getLogger(__name__)


def parse_menu(menu_dir: str) -> dict:
    log.info('Parse menu in progress...')
    weekdays = ('ПНД', 'ВТ', 'СР', 'ЧТВ', 'ПТН')
    doc: dict[str] = read_excel(menu_dir, sheet_name='Лист1', header=0).fillna('').to_dict()
    menu = dict()
    temp_key: str = ''
    temp_list: list = []
    counter: int = 0

    for column in doc.keys():
        for line in doc[column].values():
            if line and not line.startswith('Хлеб') and not line.startswith('Меню') and not line.startswith('Можно'):
                line = line.rstrip()
                if line in weekdays:
                    temp_key = line
                    temp_list = []
                    counter = 0
                    continue
                temp_list.append(line)
                counter += 1
                if counter == 4:
                    menu[temp_key] = temp_list

    new_menu: dict[str, [str, [list[str]]]] = {}
    for weekday, line in menu.items():
        soup = None
        second_course = None
        garnish = None
        salad = None
        counter = 0
        for food in line:
            if counter == 0:
                soup = food.split(' или ')
            if counter == 1:
                second_course = food.split(' или ')
            if counter == 2:
                garnish = food.split(' или ')
            if counter == 3:
                salad = food.split(' или ')
            counter += 1
        new_menu[weekday] = {
            'soup': soup,
            'second_course': second_course,
            'garnish': garnish,
            'salad': salad
        }

    log.info('Parse menu it was finished.')
    return new_menu


def get_orders(chat_id: int) -> str:
    try:
        orders: list[tuple[str, ...]] = OrderTableConnection(chat_id).get_all()
    except OperationalError as ex:
        log.error('Get orders error: %s', ex)
        if datetime.now().isoweekday() in (6, 7):
            answer = 'На выходных мы ничего не заказываем :('
        else:
            answer = 'Возникли проблемы с получением данных из таблицы.'
        return answer

    all_food: dict[str, defaultdict[str, int]] = {
        'Первое': defaultdict(int),
        'Второе': defaultdict(int),
        'Гарнир': defaultdict(int),
        'Салат': defaultdict(int),
    }

    for order in orders:
        _, first, second, garnier, salad = order
        all_food['Первое'][first] += 1
        all_food['Второе'][second] += 1
        all_food['Гарнир'][garnier] += 1
        all_food['Салат'][salad] += 1

    first = '\n'.join(f'*{food}*: {count}' for food, count in all_food['Первое'].items()) + '\n\n'
    second = '\n'.join(f'*{food}*: {count}' for food, count in all_food['Второе'].items()) + '\n\n'
    garnier = '\n'.join(f'*{food}*: {count}' for food, count in all_food['Гарнир'].items()) + '\n\n'
    salad = '\n'.join(f'*{food}*: {count}' for food, count in all_food['Салат'].items())

    return f'Всего заказов оформленных через бота: **{len(orders)}**\n\n' + first + second + garnier + salad
