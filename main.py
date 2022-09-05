from datetime import datetime
from time import sleep

import telebot
from telebot.types import Message

from environ_variables import TELEBOT_TOKEN
from validators import validate_time_command
from work_with_sheet import write_in_sheet


bot = telebot.TeleBot(TELEBOT_TOKEN)


@bot.message_handler(commands=['start'])
def get_starting(message: Message):
    bot.send_message(message.chat.id, parse_mode='HTML', text='Для включения напоминаний о заказе еды введите: <pre>/notify</pre>'
                                                              'Время упоминания по умолчанию будет 08:30. Если вы хотите изменить время,'
                                                              ' то введите: <pre>/notify 05:00</pre>')


@bot.message_handler(commands=['notify'])
def enable_notify(message: Message):
    """
    Хэндлер включения уведомлений.
    Получаем и валидируем сообщение, если все успешно - включаем бесконечный цикл,
    который напоминает про заказ еды по будням и в указанное время (если он было указано).
    В ином случае уведомляем пользователя об ошибке.
    """
    done, time_or_error = validate_time_command(message.text.split())
    if done:
        bot.send_message(message.chat.id, f'Напоминания успешно включены. Время напоминания - {time_or_error}')
        while True:
            now_time = datetime.now().strftime("%H:%M")
            weekday = datetime.now().isoweekday()

            if now_time == time_or_error and weekday not in (6, 7):
                bot.send_message(message.chat.id, 'Доброе утро! Не забываем про заказ еды. Хорошего дня.')
            sleep(60)
    else:
        bot.send_message(message.chat.id, f'Ошибка. {time_or_error}')


@bot.message_handler(commands=['order'])
def food_ordering(message: Message):
    full_string = message.text.split()
    full_name = f'{full_string[1]} {full_string[2]}'
    order = ' '.join(word for word in full_string[3:])
    if write_in_sheet(full_name, order):
        bot.send_message(message.chat.id, 'Заказ успешно сделан. Не забудьте произвести оплату.')
    else:
        bot.send_message(message.chat.id, 'Возникли проблемы при заполнении Excel таблицы.')


@bot.message_handler(content_types=['text'])
def food_is_comming(message: Message):
    """Хэндлер фраз-крючков, по нахождению которых - желаем приятного аппетита"""
    hook_words = {'поднимается', 'приехала', 'примите', 'привезли'}
    lower_message = set(map(lambda x: x.lower(), message.text.split(' ')))
    if set(lower_message).intersection(hook_words):
        with open('src/eating.gif', 'rb') as gif:
            bot.send_message(message.chat.id, 'Приятного аппетита.')
            bot.send_animation(message.chat.id, gif)


# TODO: раскомментировать, когда будет ясно как парсить эксель документ, который нам кидают каждую неделю.
# @bot.message_handler(content_types=['document'])
# def get_week_menu(message: Message):
#     """Скачиваем и парсим XLSX чтобы получить еженедельное меню в TXT формате"""
#     menu_dir = f'{os.getcwd()}/src/menus/{message.document.file_name}'
#     document = bot.download_file(bot.get_file(message.document.file_id).file_path)
#     with open(menu_dir, 'wb') as menu:
#         menu.write(document)
#     menu_text = parse_menu(menu_dir)
#     bot.send_message(message.chat.id, menu_text)

if __name__ == '__main__':
    bot.infinity_polling()
