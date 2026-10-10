import re

def parse_values(values_str: str):
    """
    Парсит строку вида: ("Sergei", 28, true)
    Возвращает: ["Sergei", 28, True]
    """
    # Убираем скобки и пробелы по краям
    values_str = values_str.strip()
    if values_str.startswith("("):
        values_str = values_str[1:]
    if values_str.endswith(")"):
        values_str = values_str[:-1]

    tokens = []
    pos = 0
    length = len(values_str)

    while pos < length:
        ch = values_str[pos]

        # Строка в двойных кавычках
        if ch == '"':
            end = values_str.find('"', pos + 1)
            if end == -1:
                raise ValueError("Незакрытая кавычка в VALUES")
            tokens.append(values_str[pos + 1:end])
            pos = end + 1

        # Число (включая отрицательное)
        elif ch.isdigit() or (ch == "-" and pos + 1 < length and values_str[pos + 1].isdigit()):
            start = pos
            while pos < length and (values_str[pos].isdigit() or values_str[pos] == "."):
                pos += 1
            num_str = values_str[start:pos].strip()
            # Пробуем сначала int, потом float
            try:
                tokens.append(int(num_str))
            except ValueError:
                tokens.append(float(num_str))

        # Булевы значения
        elif values_str[pos:pos + 4].lower() == "true":
            tokens.append(True)
            pos += 4
        elif values_str[pos:pos + 5].lower() == "false":
            tokens.append(False)
            pos += 5

        # Пропускаем запятые и пробелы
        else:
            if ch in ", \t\n":
                pos += 1
                continue
            raise ValueError(f"Неожиданный символ в VALUES: {ch}")

        # Пропускаем пробелы и запятые после токена
        while pos < length and values_str[pos] in ", \t\n":
            pos += 1

    return tokens


def parse_where(where_str: str) -> dict:
    """
    Парсит условие WHERE: age = 28 или name = "Sergei"
    Возвращает: {'age': 28} или {'name': 'Sergei'}
    """
    where_str = where_str.strip()
    match = re.match(r'^\s*(\w+)\s*=\s*(.*)$', where_str)
    if not match:
        raise ValueError(f"Некорректное условие WHERE: {where_str}")

    key = match.group(1)
    val_raw = match.group(2).strip()

    # Строка в кавычках
    if val_raw.startswith('"') and val_raw.endswith('"'):
        value = val_raw[1:-1]
    elif val_raw.lower() == "true":
        value = True
    elif val_raw.lower() == "false":
        value = False
    else:
        # Иначе считаем числом
        try:
            value = int(val_raw)
        except ValueError:
            try:
                value = float(val_raw)
            except ValueError:
                # Если совсем непонятно — оставляем строкой (на всякий случай)
                value = val_raw

    return {key: value}


def parse_set(set_str: str) -> dict:
    """
    Парсит часть SET: age = 29
    Возвращает: {'age': 29}
    """
    set_str = set_str.strip()
    match = re.match(r'^\s*(\w+)\s*=\s*(.*)$', set_str)
    if not match:
        raise ValueError(f"Некорректный SET: {set_str}")

    key = match.group(1)
    val_raw = match.group(2).strip()

    if val_raw.startswith('"') and val_raw.endswith('"'):
        value = val_raw[1:-1]
    elif val_raw.lower() == "true":
        value = True
    elif val_raw.lower() == "false":
        value = False
    else:
        try:
            value = int(val_raw)
        except ValueError:
            try:
                value = float(val_raw)
            except ValueError:
                value = val_raw

    return {key: value}
