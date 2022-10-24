import logging

from pandas import read_excel

log = logging.getLogger(__name__)


def parse_menu(menu_dir: str) -> dict:
    log.info('Parse menu in progress...')
    weekdays = ('ПНД', 'ВТ', 'СР', 'ЧТВ', 'ПТН')
    doc: dict[str] = read_excel(menu_dir, sheet_name='Лист1', header=0).fillna('').to_dict()

    assert len(doc) == 2

    menu = dict()
    first_column, second_column = doc.keys()

    temp_key: str = ''
    temp_list: list = []
    counter: int = 0

    for line in doc[first_column].values():
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

    for line in doc[second_column].values():
        if line and not line.startswith('Хлеб') and line != 'СБ' and line != ' ':
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
