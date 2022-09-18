import asyncio
import logging
import os
from datetime import datetime
from sqlite3 import OperationalError
from subprocess import run

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, Message

from db_conn import MenuTableConnection, NotifyTableConnection
from environ_variables import SPREADSHEET_ID, TELEBOT_TOKEN
from google_api import clean_orders, make_order
from order_with_buttons import Order
from parse import parse_menu
from validators import validate_time_command

bot = AsyncTeleBot(TELEBOT_TOKEN)
logging.basicConfig(format='%(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

WEEKDAYS = {
    1: "ПНД",
    2: "ВТ",
    3: "СР",
    4: "ЧТВ",
    5: "ПТН"
}
TODAY = WEEKDAYS.get(datetime.now().isoweekday())


@bot.message_handler(commands=['button'])
async def button(message: Message):
    try:
        menu = MenuTableConnection(message.chat.id).generate_order_menu(TODAY)

        markup = InlineKeyboardMarkup()
        for dish in menu['first']:
            markup.add(
                dish
            )
        answer = 'Вот меню на сегодня:'
    except TypeError:
        answer = 'На выходных мы ничего не заказываем :('
        markup = None

    await bot.send_message(message.chat.id, text=answer, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
async def callback_menu(call: CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    menu_conn = MenuTableConnection(chat_id)

    markup = InlineKeyboardMarkup()
    inline_buttons = MenuTableConnection(chat_id).generate_order_menu(TODAY)
    data, menu_index, dish_index = call.data.split('_')

    menu = menu_conn.get_menu(TODAY)
    menu_conn.create_and_insert_to_order_table(user_id=user_id)
    menu_conn.update_order_table(user_id, data, menu[int(menu_index)].split('\n')[int(dish_index)])

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
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
    except Exception:
        full_name = call.from_user.full_name
        order, msg = Order(user_id=user_id, chat_id=chat_id, full_name=full_name).make_order()
        answer = f'Заказ на имя <b>{full_name}</b> произведен успешно.\nВаш заказ:\n\n<pre>{order}</pre>\n' + f'{msg}'
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML',
                                    text=answer)


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
        db_conn = NotifyTableConnection()
        try:
            db_conn.insert_notify_table(time, message.chat.id)
        except Exception:
            log.error('Updating existing values.')
            db_conn.update_notify(time, message.chat.id)
        await bot.send_message(message.chat.id, f'Время напоминаний установлено на {time}')
    else:
        await bot.send_message(message.chat.id, error)


# TODO: удалить
@bot.message_handler(commands=['order'])
async def food_ordering(message: Message):
    full_string = message.text.split()
    full_name = f'{full_string[1]} {full_string[2]}'

    status, msg = make_order(full_name, message.text.split('\n')[1:])
    if msg:
        await bot.send_message(message.chat.id, *msg)

    if status:
        await bot.send_message(message.chat.id, f'Заказ произведен успешно. Не забудьте произвести оплату.')
        NotifyTableConnection().need_clean_table(message.chat.id, True)
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
    week_table = MenuTableConnection(message.chat.id).get_menu
    try:
        if message.text == '/menu':
            menu = '\n'.join(week_table(TODAY))
            answer = f'Меню на сегодня:\n\n' \
                     f'<pre>{menu}</pre>'
        elif message.text.split()[1].upper() in WEEKDAYS.values():
            day = message.text.split()[1]
            menu = '\n'.join(week_table(day))
            answer = f'Меню на {day}:\n\n' \
                     f'<pre>{menu}</pre>'
        else:
            answer = f'Неправильный формат команды. Убедитесь в том, что вы правильно ввели команду:\n ' \
                     f'<pre>/menu $DAY - где $DAY: ПНД, ВТ, СР, ЧТВ, ПТН</pre> ' \
                     f'Для того чтобы получить меню на сегодня: <pre>/menu</pre>'
        await bot.send_message(message.chat.id, parse_mode='HTML', text=answer)
    except OperationalError:
        await bot.send_message(message.chat.id, f'Меню для текущей недели не было загружено.')
    except TypeError:
        await bot.send_message(message.chat.id, f'К сожалению на выходных ничего не доставляют.')


@bot.message_handler(commands=['update'])
async def update(message: Message):
    await bot.send_message(message.chat.id, 'Начинаю обновление...')
    log.info(run(['git', 'restore', '.']))
    log.info(run(['git', 'fetch']))
    log.info(run(['git', 'pull']).stdout)
    log.info(run(['cp', 'contrib/gula-bot.service', '/etc/systemd/system/']))
    log.info(run(['systemctl', 'daemon-reload']))
    await bot.send_message(message.chat.id, 'Обновление выполнено успешно!')
    log.info(run(['systemctl', 'restart', 'gula-bot']))


@bot.message_handler(content_types=['text'])
async def food_is_comming(message: Message):
    """Хэндлер фраз-крючков, по нахождению которых - желаем приятного аппетита"""
    hook_words = {'поднимается', 'приехал', 'приехала', 'примите', 'привезли'}
    lower_message = set(map(lambda x: x.lower(), message.text.split(' ')))
    if set(lower_message).intersection(hook_words):
        with open('src/eating.gif', 'rb') as gif:
            await bot.send_message(message.chat.id, 'Приятного аппетита.')
            # TODO: разные гифки, пока отключаем ибо раздражает одно и тоже
            # await bot.send_animation(message.chat.id, gif)


@bot.message_handler(content_types=['document'])
async def get_new_week_menu(message: Message):
    """Скачиваем и парсим XLSX, чтобы получить еженедельное меню в TXT формате"""
    week_menu = MenuTableConnection(message.chat.id)
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


async def notify_syncer():
    log.info('Notify syncer has been started.')
    while True:
        notify_conn = NotifyTableConnection()
        now_time = datetime.now().strftime("%H:%M")
        weekday = datetime.now().isoweekday()

        if not notify_conn.get_notifications():
            await asyncio.sleep(60)

        for notify in notify_conn.get_notifications():
            if now_time.endswith('00'):
                log.info('Syncer continues its work. Notify time: %s', notify['time'])
            if not notify['enabled']:
                continue
            if weekday in (6, 7):
                if notify['need_clean'] and now_time == notify['time']:
                    clean_orders()
                    log.info('Orders has been cleaned.')
                    notify_conn.need_clean_table(notify['chat_id'], False)
                    await bot.send_message(notify['chat_id'], 'Таблица заказов успешно очищена. Хороших выходных.')
                continue
            if now_time == notify['time']:
                chat_id = notify['chat_id']
                menu = None
                try:
                    menu = '\n'.join(MenuTableConnection(chat_id).get_menu(WEEKDAYS.get(weekday)))
                except OperationalError:
                    log.error('The menu was not loaded.')
                except TypeError:
                    log.error('There is no menu for the current day of the week.')

                await bot.send_message(chat_id, 'Доброе утро! Не забываем про заказ еды. Хорошего дня.')
                if menu:
                    await bot.send_message(chat_id, parse_mode='HTML', text=f'Меню на сегодня:\n\n'
                                                                            f'<pre>{menu}</pre>')

        await asyncio.sleep(60)


async def main():
    tasks = [
        bot.polling(non_stop=True),
        notify_syncer()
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    log.info('bot was been started')
    asyncio.run(main())
