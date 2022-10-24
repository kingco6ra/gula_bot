import asyncio
import logging

from telebot.async_telebot import AsyncTeleBot

from environ_variables import TELEBOT_TOKEN
from handlers.get_starting import GetStartingHandler
from handlers.menu import MenuHandler
from handlers.notify import NotifyHandler
from handlers.order import OrderHandler
from handlers.update import UpdateHandler
from notify_syncer import NotifySyncer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s: %(message)s')
log = logging.getLogger(__name__)

HANDLERS = [
    GetStartingHandler,
    MenuHandler,
    OrderHandler,
    UpdateHandler,
    NotifyHandler,
]


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
