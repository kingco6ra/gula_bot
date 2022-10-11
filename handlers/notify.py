"""
Хэндлер отвечающий за уведомления.
"""

import logging
from sqlite3 import IntegrityError

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from database import NotifyTableConnection
from validators import validate_time_command

log = logging.getLogger(__name__)


class NotifyHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.__bot = bot
        self.__register_handlers()

    async def _enable_notify(self, message: Message):
        """
        Хэндлер включения уведомлений.
        Получаем и валидируем сообщение, если все успешно - включаем бесконечный цикл,
        который напоминает про заказ еды по будням и в указанное время (если он было указано, если нет - устанавливаем стандартное время).
        В ином случае уведомляем пользователя об ошибке.
        """
        # TODO: сделать возможность отключения уведомлений
        status, time, error = validate_time_command(message.text.split())
        if status:
            notify_conn = NotifyTableConnection()
            try:
                notify_conn.insert(time, message.chat.id)
            except IntegrityError:
                log.error('Updating existing values.')
                notify_conn.update(time, message.chat.id)
            await self.__bot.send_message(message.chat.id, f'Время напоминаний установлено на {time}')
        else:
            await self.__bot.send_message(message.chat.id, error)

    async def food_is_comming(self, message: Message):
        """Хэндлер фраз-крючков, по нахождению которых - желаем приятного аппетита"""
        hook_words = {'поднимается', 'приехал', 'приехала', 'примите', 'привезли', 'туть', 'на базе'}
        stop_words = {'?', 'не'}
        lower_message = set(map(lambda x: x.lower(), message.text.split(' ')))

        if not set(lower_message).intersection(stop_words) and set(lower_message).intersection(hook_words):
            await self.__bot.send_message(message.chat.id, 'Приятного аппетита.')

    def __register_handlers(self):
        self.__bot.register_message_handler(self._enable_notify, commands=['notify'])
        self.__bot.register_message_handler(self.food_is_comming)
