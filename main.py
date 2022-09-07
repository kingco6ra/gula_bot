import logging
import os
from datetime import datetime
from sqlite3 import OperationalError
from subprocess import run
from time import sleep

import telebot
from telebot.types import Message

from db_conn import insert_menu, get_menu, create_week_table
from environ_variables import TELEBOT_TOKEN, SPREADSHEET_ID
from parse import parse_menu
from validators import validate_time_command
from google_api import make_order, clean_orders

bot = telebot.TeleBot(TELEBOT_TOKEN)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)
weekdays = {
    1: 'ПНД',
    2: 'ВТ',
    3: 'СР',
    4: 'ЧТВ',
    5: 'ПТН'
}


@bot.message_handler(commands=['start'])
def get_starting(message: Message):
    bot.send_message(message.chat.id, parse_mode='HTML', text='Для включения напоминаний о заказе еды введите: <pre>/notify</pre>'
                                                              'Время упоминания по умолчанию будет 08:30. Если вы хотите изменить время,'
                                                              ' то введите: <pre>/notify 05:00</pre>')
    bot.send_message(message.chat.id, text=f'Ссылка на таблицу для ручного оформления заказа: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')


@bot.message_handler(commands=['notify'])
def enable_notify(message: Message):
    """
    Хэндлер включения уведомлений.
    Получаем и валидируем сообщение, если все успешно - включаем бесконечный цикл,
    который напоминает про заказ еды по будням и в указанное время (если он было указано, если нет - устанавливаем стандартное время).
    В ином случае уведомляем пользователя об ошибке.
    """
    status, alert_time, error = validate_time_command(message.text.split())
    table_is_clean = True
    if status:
        bot.send_message(message.chat.id, f'Напоминания успешно включены. Время напоминания - {alert_time}')
        while True:
            now_time = datetime.now().strftime("%H:%M")
            weekday = datetime.now().isoweekday()

            if now_time == alert_time and weekday not in (6, 7):
                bot.send_message(message.chat.id, 'Доброе утро! Не забываем про заказ еды. Хорошего дня.')
                try:
                    # TODO: улучшить вывод
                    menu = '\n'.join(get_menu(weekdays.get(weekday)).split(' | '))
                    bot.send_message(message.chat.id, parse_mode='HTML', text=f'Вот меню на сегодня: \n <pre>{menu}</pre>')
                except OperationalError:
                    pass
                table_is_clean = False
            if weekday == 6 and not table_is_clean:
                clean_orders()
                bot.send_message(message.chat.id, 'Таблица заказов была успешно очищена. Хороших Выходных')
            sleep(60)
    else:
        bot.send_message(message.chat.id, parse_mode='HTML', text=f'Ошибка. {error}')


@bot.message_handler(commands=['order'])
def food_ordering(message: Message):
    full_string = message.text.split()
    full_name = f'{full_string[1]} {full_string[2]}'

    status, msg = make_order(full_name, message.text.split('\n')[1:])
    if msg:
        bot.send_message(message.chat.id, *msg)

    if status:
        bot.send_message(message.chat.id, 'Заказ произведен успешно. Не забудьте произвести оплату.')
    else:
        bot.send_message(message.chat.id, 'Возникли проблемы при заполнении таблицы.')


@bot.message_handler(commands=['help'])
def get_help(message: Message):
    bot.send_message(message.chat.id, parse_mode='HTML', text=f'Как сделать заказ:\n'
                                                              '<pre>'
                                                              '/order Пупкин В.\n'
                                                              'ПН: мясо, курица, рыба\n'
                                                              'ЧТ: суп, второе, салат'
                                                              '</pre>'
                                                              'Я и автоматически запишу заказ в таблицу:')
    with open('src/help.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['menu'])
def get_week_menu(message: Message):
    """Получаем меню"""
    today = datetime.now().isoweekday()
    try:
        weekday = message.text.split()[1].upper()
        weekday = weekday if weekday in weekdays.values() else weekdays.get(today)
        menu = '\n'.join(get_menu(weekday).split(' | '))
    except IndexError:
        menu = '\n'.join(get_menu(weekdays.get(today)).split(' | '))

    bot.send_message(message.chat.id, parse_mode='HTML', text=f'<pre>{menu}</pre>')


@bot.message_handler(commands=['update'])
def update(message: Message):
    bot.send_message(message.chat.id, 'Начинаю обновление...')
    log.info(run(['git', 'restore', '.']))
    log.info(run(['git', 'fetch']))
    log.info(run(['git', 'pull']).stdout)
    log.info(run(['cp', 'gula-bot.service', '/etc/systemd/system/']))
    bot.send_message(message.chat.id, 'Обновление выполнено успешно!')
    log.info(run(['systemctl', 'restart', 'gula-bot']))


@bot.message_handler(content_types=['text'])
def food_is_comming(message: Message):
    """Хэндлер фраз-крючков, по нахождению которых - желаем приятного аппетита"""
    hook_words = {'поднимается', 'приехал', 'приехала', 'примите', 'привезли'}
    lower_message = set(map(lambda x: x.lower(), message.text.split(' ')))
    if set(lower_message).intersection(hook_words):
        with open('src/eating.gif', 'rb') as gif:
            bot.send_message(message.chat.id, 'Приятного аппетита.')
            bot.send_animation(message.chat.id, gif)


@bot.message_handler(content_types=['document'])
def get_new_week_menu(message: Message):
    """Скачиваем и парсим XLSX чтобы получить еженедельное меню в TXT формате"""
    menu_dir = f'{os.getcwd()}/src/menus/{message.document.file_name}'
    document = bot.download_file(bot.get_file(message.document.file_id).file_path)
    with open(menu_dir, 'wb') as menu:
        menu.write(document)
    try:
        create_week_table()
        insert_menu(parse_menu(menu_dir))
        bot.send_message(message.chat.id, 'Меню было успешно занесено в базу данных.')
    except OperationalError:
        bot.send_message(message.chat.id, 'Меню для этой недели уже загружено в базу данных.')


if __name__ == '__main__':
    log.info('bot was been started')
    bot.infinity_polling()
