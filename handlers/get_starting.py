"""
Хэндлер отвечающий за команду /start и /help.
/start - мини-экскурс как включить уведомления и ссылка на таблицу.
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
        help_text = f'''
Заказ можно совершить *тремя способами*:

*1. Руками заполнить таблицу.* 
_Таблица с меню на неделю находится на втором листе._
        
*2. Ввести в этом чате:*

`/order Пупкин В.`
`ПНД: мясо, курица, рыба`
`ЧТВ: мясо, курица, рыба`
        
*Пупкин В.* - _Ваша фамилия и инициал имени._
*ПНД* - _день недели (ПНД, ВТ, СР, ЧТВ, ПТН)._
                
3. Ввести в этом чате `/заказ` для *кнопочного* оформления заказа. Этот способ, _пока что_, доступен только для заказа *день в день*.

Бот автоматически попытается найти Вас в таблице по фамилии, имени, или по *Telegram ID*.
Если у него не получится это сделать - он запишет Вас в таблицу так, как вы записаны в телеграмме и добавит к имени Ваш, персональный, *Telegram ID*.

Если вы уже есть в таблице, и Ваше имя в телеграмме *не совпадает* с именем в таблице, - вы можете ввести: `/id`, \
и добавить полученное число к Вашему имени в таблице. 
Это нужно сделать только *один раз*.
'''

        await self.__bot.send_message(message.chat.id, parse_mode='Markdown', text=help_text)
        with open('src/help.jpg', 'rb') as photo:
            await self.__bot.send_photo(message.chat.id, photo)

    async def id(self, message: Message):
        await self.__bot.send_message(
            message.chat.id, reply_to_message_id=message.message_id, parse_mode='Markdown', text=f'Ваш *Telegram ID* - `{message.from_user.id}`'
        )

    def __register_handlers(self):
        self.__bot.register_message_handler(self.start, commands=['start'])
        self.__bot.register_message_handler(self.help, commands=['help'])
        self.__bot.register_message_handler(self.id, commands=['id'])
