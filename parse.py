"""
TODO: из-за того, что присылают кривой эксель документ, распарсить его правильно, и при этом ничего не потерять, - является интересной задачей.

"""
from pandas import read_excel


def parse_menu(menu_dir: str) -> dict:
    weekdays = ('ПНД', 'ВТ', 'СР', 'ЧТВ', 'ПТН')
    doc: dict[str] = read_excel(menu_dir, sheet_name='Лист1', header=0).fillna('').to_dict()
    menu = dict()

    temp_key: str = ''
    temp_list: list = []
    counter: int = 0
    for line in doc['Unnamed: 0'].values():
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

    for line in doc['Unnamed: 2'].values():
        if line and not line.startswith('Хлеб') and line != 'СБ':
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
    return menu
