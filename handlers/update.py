"""
Хэндлер отвечающий за команду обновления.
Обновление возможно только, если бот был склонирован с GitHub.
"""

import logging
from subprocess import run

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

log = logging.getLogger(__name__)


class UpdateHandler:
    def __init__(self, bot: AsyncTeleBot):
        self.__bot = bot
        self.__register_handlers()

    async def update(self, message: Message):
        await self.__bot.send_message(message.chat.id, 'Начинаю обновление...')
        log.info(run(['git', 'restore', '.']))
        log.info(run(['git', 'fetch']))
        log.info(run(['git', 'pull']).stdout)
        log.info(run(['cp', 'contrib/gula-bot.service', '/etc/systemd/system/']))
        log.info(run(['systemctl', 'daemon-reload']))
        await self.__bot.send_message(message.chat.id, 'Обновление выполнено успешно!')
        log.info(run(['systemctl', 'restart', 'gula-bot']))

    def __register_handlers(self):
        self.__bot.register_message_handler(self.update, commands=['update'])
