"""
Файл с валидаторами. Возможно в будущем здесь появится что-то еще. Возможно нет.
"""


def validate_time_command(command: list) -> tuple[bool, str]:
    print(command)
    if command[0] == '/notify' and len(command) == 1:
        return True, '08:30'

    try:
        hrs, mins = map(lambda x: int(x), command[1].split(':'))
    except ValueError:
        return False, 'Неправильный формат времени.'
    if len(command) > 2:
        return False, 'Неправильный формат сообщения.'
    elif hrs > 24 or mins > 60:
        return False, 'Неправильный формат времени.'
    return True, f'{hrs}:{mins}'

