"""
Файл с валидаторами. Возможно в будущем здесь появится что-то еще. Возможно нет.
"""


def validate_time_command(command: list) -> tuple[bool, str, str | None]:
    default_time = '09:00'
    if command[0] == '/notify' and len(command) == 1:
        return True, default_time, None
    time = command[1]
    wrong_time_format = 'Неправильный формат времени или сообщения.' \
                        ' Время должно быть в 24 часовом формате, с учетом нолей. Сообщение правильного формата:' \
                        ' <pre>/notify 04:04</pre>' \
                        'Также вы можете ввести: ' \
                        '<pre>/notify</pre>' \
                        'Для того чтобы установить напоминания на 09:00.'

    try:
        hrs, mins = map(lambda x: int(x), time.split(':'))
    except ValueError:
        return False, default_time, wrong_time_format
    if len(command) > 2 or hrs > 24 or mins > 60 or len(time) != 5:
        return False, default_time, wrong_time_format
    return True, time, None

