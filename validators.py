"""
Файл с валидаторами. Возможно в будущем здесь появится что-то еще. Возможно нет.
"""


def validate_time_command(command: list) -> tuple[bool, str, str | None]:
    default_time = '09:00'
    if command[0] == '/notify' and len(command) == 1:
        return True, default_time, None
    time = command[1]
    try:
        hrs, mins = map(lambda x: int(x), time.split(':'))
    except ValueError:
        return False, default_time, 'Неправильный формат времени.'
    if len(command) > 2:
        return False, default_time, 'Неправильный формат сообщения.'
    elif hrs > 24 or mins > 60:
        return False, default_time, 'Неправильный формат времени.'
    return True, time, None

