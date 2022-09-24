"""
Хэндлер отвечающий за команду /start и /help.
/start - мини-экскурс как включить уведомления и ссылка на таблицу.
# TODO: обновить /help когда будут введены кнопки.
/help - как сделать заказ.
"""
import os

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

SPREADSHEET_ID = os.environ['SPREADSHEET_ID']


class GetStartingHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.__bot = bot
        self.__register_handlers()

    async def start(self, message: Message):
        await self.__bot.send_message(message.chat.id, parse_mode='HTML', text='Для включения напоминаний о заказе еды введите: <pre>/notify</pre>'
                                                                               'Время упоминания по умолчанию будет 08:30. '
                                                                               'Если вы хотите изменить время,'
                                                                               ' то введите: <pre>/notify 05:00</pre>')
        await self.__bot.send_message(message.chat.id,
                                      text=f'Ссылка на таблицу для ручного оформления заказа: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')

    async def help(self, message: Message):
        await self.__bot.send_message(message.chat.id, parse_mode='HTML', text=f'Как сделать заказ:\n'
                                                                               '<pre>'
                                                                               '/order Пупкин В.\n'
                                                                               'ПНД: мясо, курица, рыба\n'
                                                                               'ЧТВ: суп, второе, салат'
                                                                               '</pre>'
                                                                               'И я автоматически запишу заказ в таблицу:')
        with open('src/help.jpg', 'rb') as photo:
            await self.__bot.send_photo(message.chat.id, photo)

    def __register_handlers(self):
        self.__bot.register_message_handler(self.start, commands=['start'])
        self.__bot.register_message_handler(self.help, commands=['help'])
