from telebot.async_telebot import AsyncTeleBot


# TODO: сделать нормальный базовый класс для всех хэндлеров.
# включая callback, и hook-words
class BaseHandler:
    def __init__(self, bot: AsyncTeleBot, methods: list[str]):
        self.__bot = bot
        self.__methods = [method for method in methods if not method.startswith('_')]
        self.__register_handlers()

    def __register_handlers(self):
        for method in self.__methods:
            func_name = getattr(self.__class__, method)
            self.__bot.register_message_handler(func_name, commands=[method])
