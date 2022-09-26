"""
Хэндлер отвечающий за команды заказов:
    /button - заказ с помощью кнопок TODO: переименовать.
    /order - заказ с помощью письменной команды.
    /menu - получение меню.
"""
from datetime import datetime
from sqlite3 import OperationalError

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import CallbackQuery, InlineKeyboardMarkup, Message

from database import MenuTableConnection, NotifyTableConnection, OrderTableConnection
from google_api import GoogleSheets
from order_with_buttons import ButtonOrder

WEEKDAYS = {
    1: "ПНД",
    2: "ВТ",
    3: "СР",
    4: "ЧТВ",
    5: "ПТН"
}
TODAY = WEEKDAYS.get(datetime.now().isoweekday())


class OrderHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.__bot = bot
        self.__register_handlers()

    async def order_button(self, message: Message):
        try:
            menu = OrderTableConnection(message.chat.id).get_menu_markup(TODAY)

            markup = InlineKeyboardMarkup()
            for dish in menu['first']:
                markup.add(
                    dish
                )
            answer = f'`Пожалуйста, не нажимайте на это меню, если его вызвали не вы.` \n\n' \
                     f'*Вот меню на сегодня:*'
        except TypeError:
            answer = 'На выходных мы ничего не заказываем :('
            markup = None
        except OperationalError:
            answer = 'Нет данных по таблице.'
            markup = None

        await self.__bot.send_message(message.chat.id, parse_mode='Markdown', text=answer, reply_markup=markup)

    async def callback_menu(self, call: CallbackQuery):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        order_conn = OrderTableConnection(chat_id)

        markup = InlineKeyboardMarkup()
        inline_buttons = OrderTableConnection(chat_id).get_menu_markup(TODAY)
        data, menu_index, dish_index = call.data.split('_')

        menu = MenuTableConnection(chat_id).get_menu(TODAY)
        order_conn.create_and_insert(user_id=user_id)
        order_conn.update(user_id, data, menu[int(menu_index)].split('\n')[int(dish_index)])

        if data == 'first':
            inline_buttons = inline_buttons['second']
        if data == 'second':
            inline_buttons = inline_buttons['garnier']
        if data == 'garnier':
            inline_buttons = inline_buttons['salad']
        if data == 'salad':
            inline_buttons = inline_buttons['salad']

        for item in inline_buttons:
            markup.add(item)
        try:
            await self.__bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        except ApiTelegramException:
            first_name = call.from_user.first_name
            last_name = call.from_user.last_name
            full_name = f'{last_name} {first_name}' if last_name else first_name

            order, msg = ButtonOrder(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name).make_order()
            answer = f'Заказ на имя <b>{full_name}</b> произведен успешно.\nВаш заказ:\n\n<pre>{order}</pre>\n' + f'{msg}'
            await self.__bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML',
                                               text=answer)

    async def order(self, message: Message):
        full_string = message.text.split()
        full_name = f'{full_string[1].capitalize()} {full_string[2].capitalize()}'

        status, msg = GoogleSheets().make_order(full_name, message.text.split('\n')[1:])
        if msg:
            await self.__bot.send_message(message.chat.id, *msg)

        if status:
            await self.__bot.send_message(message.chat.id, f'Заказ произведен успешно. Не забудьте произвести оплату.')
            NotifyTableConnection().need_clean_table(message.chat.id, True)
        else:
            await self.__bot.send_message(message.chat.id, 'Возникли проблемы при заполнении таблицы.')

    def __register_handlers(self):
        self.__bot.register_message_handler(self.order, commands=['order'])
        self.__bot.register_message_handler(self.order_button, commands=['заказ'])
        self.__bot.register_callback_query_handler(self.callback_menu, func=lambda call: True)
