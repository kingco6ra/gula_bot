"""
Хэндлер отвечающий за загрузку меню в базу данных.
"""

import logging
import os
from datetime import datetime
from sqlite3 import OperationalError

from telebot.async_telebot import AsyncTeleBot
from telebot.types import File, Message

from database import MenuTableConnection
from google_api import GoogleSheets
from parse import parse_menu

log = logging.getLogger(__name__)
WEEKDAYS = {
    1: "ПНД",
    2: "ВТ",
    3: "СР",
    4: "ЧТВ",
    5: "ПТН"
}
TODAY = WEEKDAYS.get(datetime.now().isoweekday())


class MenuHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.__bot = bot
        self.__register_handlers()

    async def get_new_week_menu(self, message: Message):
        """Скачиваем и парсим XLSX, чтобы получить еженедельное меню в TXT формате"""
        start_message = await self.__bot.send_message(message.chat.id, text='⏳ Заношу меню в базу данных и в таблицу.\nЭто может занять несколько секунд.')
        menu_conn = MenuTableConnection(message.chat.id)
        menu_dir = f'{os.getcwd()}/src/menus/{message.document.file_name}'
        file: File = await self.__bot.get_file(message.document.file_id)
        document = await self.__bot.download_file(file.file_path)
        with open(menu_dir, 'wb') as menu:
            menu.write(document)
        try:
            menu_conn.create()
            menu = parse_menu(menu_dir)
            menu_conn.insert_menu(menu)
            answer = '✅ Меню было успешно занесено в базу данных.'
            GoogleSheets().write_menu(menu_conn.get_all_menu())
        except OperationalError as error:
            log.error(error)
            answer = '❌ Произошла ошибка.'

        await self.__bot.edit_message_text(text=answer, chat_id=message.chat.id, message_id=start_message.message_id, parse_mode='HTML')

    async def menu(self, message: Message):
        """
        /order - получить сегодняшнее меню
        /order ПНД - получить меню на понедельник
        :param message:
        :return:
        """
        week_table = MenuTableConnection(message.chat.id).get_menu
        try:
            if message.text == '/menu':
                menu = '\n'.join(week_table(TODAY))
                answer = f'Меню на сегодня:\n\n' \
                         f'<pre>{menu}</pre>'
            elif message.text.split()[1].upper() in WEEKDAYS.values():
                day = message.text.split()[1].upper()
                menu = '\n'.join(week_table(day))
                answer = f'Меню на {day}:\n\n' \
                         f'<pre>{menu}</pre>'
            else:
                answer = f'Неправильный формат команды. Убедитесь в том, что вы правильно ввели команду:\n ' \
                         f'<pre>/menu $DAY - где $DAY: ПНД, ВТ, СР, ЧТВ, ПТН</pre> ' \
                         f'Для того чтобы получить меню на сегодня: <pre>/menu</pre>'
            await self.__bot.send_message(message.chat.id, parse_mode='HTML', text=answer)
        except OperationalError:
            await self.__bot.send_message(message.chat.id, f'Меню для текущей недели не было загружено.')
        except TypeError:
            await self.__bot.send_message(message.chat.id, f'К сожалению на выходных ничего не доставляют.')

    def __register_handlers(self):
        self.__bot.register_message_handler(self.menu, commands=['menu'])
        self.__bot.register_message_handler(self.get_new_week_menu, content_types=['document'])
