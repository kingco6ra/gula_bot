"""
TODO: из-за того, что присылают кривой эксель документ, распарсить его правильно, и при этом ничего не потерять, - является интересной задачей.

"""
from pandas import read_excel


def parse_menu(menu_dir: str) -> str:
    doc = read_excel(menu_dir, sheet_name='Лист1', header=0)
    menu = str()

    return menu
