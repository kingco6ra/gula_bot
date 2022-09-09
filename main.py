import asyncio
import logging
import os
from datetime import datetime
from sqlite3 import OperationalError
from subprocess import run

from aiofile import async_open
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from db_conn import DataBaseConnection
from environ_variables import TELEBOT_TOKEN, SPREADSHEET_ID
from google_api import make_order
from parse import parse_menu
from validators import validate_time_command

bot = AsyncTeleBot(TELEBOT_TOKEN)
logging.basicConfig(format='%(message)s', level=logging.INFO)
log = logging.getLogger(__name__)
weekdays = {
    1: 'ПНД',
    2: 'ВТ',
    3: 'СР',
    4: 'ЧТВ',
    5: 'ПТН'
}


@bot.message_handler(commands=['start'])
async def get_starting(message: Message):
    await bot.send_message(message.chat.id, parse_mode='HTML', text='Для включения напоминаний о заказе еды введите: <pre>/notify</pre>'
                                                                    'Время упоминания по умолчанию будет 08:30. Если вы хотите изменить время,'
                                                                    ' то введите: <pre>/notify 05:00</pre>')
    await bot.send_message(message.chat.id, text=f'Ссылка на таблицу для ручного оформления заказа: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')


@bot.message_handler(commands=['notify'])
async def enable_notify(message: Message):
    """
    Хэндлер включения уведомлений.
    Получаем и валидируем сообщение, если все успешно - включаем бесконечный цикл,
    который напоминает про заказ еды по будням и в указанное время (если он было указано, если нет - устанавливаем стандартное время).
    В ином случае уведомляем пользователя об ошибке.
    """
    # TODO: сделать возможность отключения уведомлений
    status, time, error = validate_time_command(message.text.split())
    if status:
        db_conn = DataBaseConnection(message.chat.id)
        status = db_conn.create_notify_table(time)
        if not status:
            db_conn.change_notify(time)
        await bot.send_message(message.chat.id, f'Время напоминаний установлено на {time}')
    else:
        await bot.send_message(message.chat.id, error)


@bot.message_handler(commands=['order'])
async def food_ordering(message: Message):
    full_string = message.text.split()
    full_name = f'{full_string[1]} {full_string[2]}'

    status, msg = make_order(full_name, message.text.split('\n')[1:])
    if msg:
        await bot.send_message(message.chat.id, *msg)

    if status:
        await bot.send_message(message.chat.id, f'Заказ произведен успешно. Не забудьте произвести оплату.\n'
                                                f'Таблица заказов: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')
    else:
        await bot.send_message(message.chat.id, 'Возникли проблемы при заполнении таблицы.')


@bot.message_handler(commands=['help'])
async def get_help(message: Message):
    await bot.send_message(message.chat.id, parse_mode='HTML', text=f'Как сделать заказ:\n'
                                                                    '<pre>'
                                                                    '/order Пупкин В.\n'
                                                                    'ПНД: мясо, курица, рыба\n'
                                                                    'ЧТВ: суп, второе, салат'
                                                                    '</pre>'
                                                                    'И я автоматически запишу заказ в таблицу:')
    with open('src/help.jpg', 'rb') as photo:
        await bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['menu'])
async def get_week_menu(message: Message):
    """
    /order - получить сегодняшнее меню
    /order ПНД - получить меню на понедельник
    :param message:
    :return:
    """
    today = weekdays.get(datetime.now().isoweekday())
    week_table = DataBaseConnection(message.chat.id).get_menu
    try:
        if message.text == '/menu':
            menu = '\n'.join(week_table(today))
            answer = f'Меню на сегодня:\n\n' \
                     f'<pre>{menu}</pre>'
        elif message.text.split()[1].upper() in weekdays.values():
            day = message.text.split()[1]
            menu = '\n'.join(week_table(day))
            answer = f'Меню на {day}:\n\n' \
                     f'<pre>{menu}</pre>'
        else:
            answer = f'Неправильный формат команды. Убедитесь в том, что вы правильно ввели команду:\n ' \
                     f'<pre>/menu $DAY - где $DAY: ПТН, ВТ, СР, ЧТВ, ПНД</pre> ' \
                     f'Для того чтобы получить меню на сегодня: <pre>/menu</pre>'
        await bot.send_message(message.chat.id, parse_mode='HTML', text=answer)
    except OperationalError:
        await bot.send_message(message.chat.id, f'Меню для текущей недели не было загружено.')


@bot.message_handler(commands=['update'])
async def update(message: Message):
    await bot.send_message(message.chat.id, 'Начинаю обновление...')
    log.info(run(['git', 'restore', '.']))
    log.info(run(['git', 'fetch']))
    log.info(run(['git', 'pull']).stdout)
    log.info(run(['cp', 'gula-bot.service', '/etc/systemd/system/']))
    await bot.send_message(message.chat.id, 'Обновление выполнено успешно!')
    log.info(run(['systemctl', 'daemon-reload']))
    log.info(run(['systemctl', 'restart', 'gula-bot']))


@bot.message_handler(content_types=['text'])
async def food_is_comming(message: Message):
    """Хэндлер фраз-крючков, по нахождению которых - желаем приятного аппетита"""
    hook_words = {'поднимается', 'приехал', 'приехала', 'примите', 'привезли'}
    lower_message = set(map(lambda x: x.lower(), message.text.split(' ')))
    if set(lower_message).intersection(hook_words):
        with open('src/eating.gif', 'rb') as gif:
            await bot.send_message(message.chat.id, 'Приятного аппетита.')
            await bot.send_animation(message.chat.id, gif)


async def notify(message: Message):
    db_conn = DataBaseConnection(message.chat.id)
    while True:
        print(db_conn.get_notify())
        await asyncio.sleep(5)


@bot.message_handler(content_types=['document'])
async def get_new_week_menu(message: Message):
    """Скачиваем и парсим XLSX чтобы получить еженедельное меню в TXT формате"""
    week_menu = DataBaseConnection(message.chat.id)
    menu_dir = f'{os.getcwd()}/src/menus/{message.document.file_name}'
    file: types.File = await bot.get_file(message.document.file_id)
    document = await bot.download_file(file.file_path)
    with open(menu_dir, 'wb') as menu:
        menu.write(document)
    try:
        week_menu.create_week_table()
        menu = parse_menu(menu_dir)
        week_menu.insert_menu(menu)
        answer = 'Меню было успешно занесено в базу данных.'
    except OperationalError:
        log.error('Menu for this week already written.')
        answer = 'Меню для этой недели уже загружено в базу данных.'
    await bot.send_message(message.chat.id, parse_mode='HTML', text=answer)

    # костыль, нужно фиксить
    # без перезапуска при вызове любой другой команды после загрузки меню:
    # 2022-09-08 19:51:23,488 (asyncio_helper.py:80 MainThread) ERROR - TeleBot: "Aiohttp ClientError: ClientOSError"
    # Aiohttp ClientError: ClientOSError
    # 2022-09-08 19:51:23,488 (async_telebot.py:317 MainThread) ERROR - TeleBot: "Request timeout. Request: method=get url=getUpdates params=<aiohttp.formdata.FormData object at 0x7fbafb6ca290> files=None request_timeout=None"
    # Request timeout. Request: method=get url=getUpdates params=<aiohttp.formdata.FormData object at 0x7fbafb6ca290> files=None request_timeout=None
    # 2022-09-08 19:51:23,488 (async_telebot.py:276 MainThread) ERROR - TeleBot: "Infinity polling: polling exited"
    # Infinity polling: polling exited
    # 2022-09-08 19:51:23,488 (async_telebot.py:278 MainThread) ERROR - TeleBot: "Break infinity polling"
    # Break infinity polling
    run(['systemctl', 'restart', 'gula-bot'])


async def main():
    tasks = [
        bot.infinity_polling(logger_level=logging.INFO),
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    log.info('bot was been started')
    asyncio.run(main())
