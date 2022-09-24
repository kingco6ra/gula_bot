import asyncio
import logging

from telebot.async_telebot import AsyncTeleBot

from environ_variables import TELEBOT_TOKEN
from handlers.get_starting import GetStartingHandler
from handlers.menu import NewWeekMenuHandler
from handlers.notify import NotifyHandler
from handlers.order import OrderHandler
from notify_syncer import NotifySyncer

HANDLERS = [
    GetStartingHandler,
    OrderHandler,
    NotifyHandler,
    NewWeekMenuHandler,
]

logging.basicConfig(format='%(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


async def main():
    tasks = [
        bot.polling(non_stop=True),
        NotifySyncer(bot).notify_syncer()
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    bot = AsyncTeleBot(TELEBOT_TOKEN)
    log.info('Bot was been started')

    for handler in HANDLERS:
        log.info('Load %s', handler.__name__)
        handler(bot)

    asyncio.run(main())
