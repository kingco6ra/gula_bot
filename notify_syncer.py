import asyncio
import logging as log
from datetime import datetime
from sqlite3 import OperationalError

from database import MenuTableConnection, NotifyTableConnection
from google_api import GoogleSheets
from telebot.async_telebot import AsyncTeleBot

WEEKDAYS = {
    1: "ПНД",
    2: "ВТ",
    3: "СР",
    4: "ЧТВ",
    5: "ПТН"
}


class NotifySyncer:
    def __init__(self, bot: AsyncTeleBot):
        self.__bot = bot
        self.__wekday = WEEKDAYS.get(datetime.now().isoweekday())
        self.__menu = MenuTableConnection
        self.__notify_conn = NotifyTableConnection()

    async def notify_syncer(self):
        log.info('Notify syncer has been started.')
        now_time = datetime.now().strftime("%H:%M")

        if not self.__notify_conn.get_notifications():
            await asyncio.sleep(60)

        for notify in self.__notify_conn.get_notifications():
            log.debug('Syncer continues its work')
            if not notify['enabled']:
                continue
            if self.__wekday in (6, 7):
                if notify['need_clean'] and now_time == notify['time']:
                    GoogleSheets().clean_orders()
                    log.info('Orders has been cleaned.')
                    self.__notify_conn.need_clean_table(notify['chat_id'], False)
                    await self.__bot.send_message(notify['chat_id'], 'Таблица заказов успешно очищена. Хороших выходных.')
                continue
            if now_time == notify['time']:
                chat_id = notify['chat_id']
                menu = self.__menu(chat_id).get_menu(self.__wekday)
                try:
                    menu = '\n'.join(menu)
                except OperationalError:
                    log.error('The menu was not loaded.')
                except TypeError:
                    log.error('There is no menu for the current day of the week.')

                await self.__bot.send_message(chat_id, 'Доброе утро! Не забываем про заказ еды. Хорошего дня.')
                if menu:
                    await self.__bot.send_message(chat_id, parse_mode='HTML', text=f'Меню на сегодня:\n\n'
                                                                                   f'<pre>{menu}</pre>')

        await asyncio.sleep(60)
        await self.notify_syncer()
