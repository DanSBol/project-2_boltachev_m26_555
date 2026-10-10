"""Функции для разбора литералов, значений вставки и условий where."""


def _is_quoted_string(s):
    """Проверяет, является ли строка литералом в кавычках."""
    if len(s) < 2:
        return False
    starts_with_double = s.startswith('"') and s.endswith('"')
    starts_with_single = s.startswith("'") and s.endswith("'")
    return starts_with_double or starts_with_single


def _try_parse_number(s):
    """Пытается распарсить число; возвращает None, если не получилось."""
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return None


def _parse_bool_literal(s):
    """Пытается распознать true/false; возвращает None, если не совпадает."""
    lower = s.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    return None


def _parse_string_literal(s):
    """Если строка в кавычках — возвращает содержимое без кавычек, иначе None."""
    if _is_quoted_string(s):
        return s[1:-1]
    return None


def _parse_list_literal(s, parse_item):
    """Парсит [...] литерал; возвращает None, если формат не совпадает."""
    if not (s.startswith("[") and s.endswith("]")):
        return None
    inner = s[1:-1].strip()
    if not inner:
        return []
    return _parse_comma_separated_list(inner, parse_item=parse_item)


def _parse_tuple_literal(s, parse_item):
    """Парсит (...) литерал; возвращает None, если формат не совпадает."""
    if not (s.startswith("(") and s.endswith(")")):
        return None
    inner = s[1:-1].strip()
    if inner == "":
        return ()
    if "," not in inner:
        # Одиночный элемент
        return (_parse_simple_literal(inner),)
    return tuple(_parse_comma_separated_list(inner, parse_item=parse_item))


def _parse_dict_literal_wrapper(s):
    """Парсит {...} литерал; возвращает None, если формат не совпадает."""
    if not (s.startswith("{") and s.endswith("}")):
        return None
    return _parse_dict_literal(s[1:-1])


def _parse_simple_literal(s):
    """Парсит литерал: булевы значения, строки, числа, списки, кортежи, словари."""
    s = s.strip()
    if not s:
        raise ValueError("Пустой литерал")

    # Булевы
    result = _parse_bool_literal(s)
    if result is not None:
        return result

    # Строки
    result = _parse_string_literal(s)
    if result is not None:
        return result

    # Числа
    result = _try_parse_number(s)
    if result is not None:
        return result

    # Списки
    result = _parse_list_literal(s, parse_item=_parse_simple_literal)
    if result is not None:
        return result

    # Кортежи
    result = _parse_tuple_literal(s, parse_item=_parse_simple_literal)
    if result is not None:
        return result

    # Словари
    result = _parse_dict_literal_wrapper(s)
    if result is not None:
        return result

    raise ValueError(f"Неподдерживаемый литерал: {s}")


class SplitterState:
    """Состояние парсера при разбиении по запятым (скобки, кавычки)."""

    __slots__ = ("depth", "in_quote")

    def __init__(self):
        self.depth = 0
        self.in_quote = None


def _update_splitter_state(state, ch):
    """Обновляет состояние парсера по одному символу."""
    if ch in ('"', "'"):
        if state.in_quote is None:
            state.in_quote = ch
        elif state.in_quote == ch:
            state.in_quote = None
        return

    if ch in ("[", "{", "("):
        if state.in_quote is None:
            state.depth += 1
        return

    if ch in ("]", "}", ")"):
        if state.in_quote is None:
            state.depth -= 1
        return


def _split_by_comma_outside_brackets(text):
    """Разбивает строку по запятым, игнорируя запятые внутри скобок и кавычек."""
    parts = []
    current = []  # список для накопления символов текущей части
    state = SplitterState()

    for ch in text:
        if ch == "," and state.in_quote is None and state.depth == 0:
            parts.append("".join(current).strip())
            current.clear()
        else:
            _update_splitter_state(state, ch)
            current.append(ch)

    last = "".join(current).strip()
    if last:
        parts.append(last)

    return parts


def _parse_comma_separated_list(text, parse_item):
    """Парсит список через запятую с учётом скобок и кавычек."""
    result = []
    parts = _split_by_comma_outside_brackets(text)

    for part in parts:
        if not part:
            continue
        result.append(parse_item(part))
    return result


def _parse_dict_literal(inner):
    """Парсит {key: value, key2: value2} в упрощённом режиме."""
    inner = inner.strip()
    if not inner:
        return {}

    pairs = _split_by_comma_outside_brackets(inner)
    result = {}

    for pair in pairs:
        pair = pair.strip()
        if ":" not in pair:
            raise ValueError(f"Некорректная пара ключ-значение: {pair}")
        key_part, _, val_part = pair.partition(":")
        key = _parse_simple_literal(key_part.strip())
        val = _parse_simple_literal(val_part.strip())
        result[key] = val

    return result


def parse_values(values_str):
    """Парсит строку значений в список/кортеж/словарь литералов."""
    if not values_str or not values_str.strip():
        raise ValueError("Пустая строка значений")

    try:
        result = _parse_simple_literal(values_str.strip())
    except Exception as e:
        msg = (
            f"Неверный формат значений: '{values_str}'. "
            "Ожидаются литералы, например: ('Alice', 30), [1, 2, 3], {'age': 29}"
        )
        raise ValueError(msg) from e

    if isinstance(result, (list, tuple, dict)):
        return result
    return [result]


def normalize_value(raw_value):
    """Приводит строковые значения: true/false к булеву, остальное — strip()."""
    if isinstance(raw_value, str):
        lower = raw_value.lower()
        if lower in ("true", "false"):
            return lower == "true"
        return raw_value.strip()
    return raw_value


def parse_insert_row(values_input):
    """Парсит строку вставки в список значений строки."""
    raw_data = parse_values(values_input)

    if isinstance(raw_data, dict):
        return list(raw_data.values())

    if isinstance(raw_data, (list, tuple)):
        return [normalize_value(v) for v in raw_data]

    return [normalize_value(raw_data)]


def parse_where_clause(where_input):
    """Парсит условие key=value в словарь с приведением типов."""
    if not where_input:
        return {}

    where_input = where_input.strip()

    if "=" in where_input:
        key, _, val = where_input.partition("=")
        key = key.strip()
        val_raw = val.strip()

        try:
            val = _parse_simple_literal(val_raw)
        except ValueError:
            # Если парсинг не прошёл, пробуем просто убрать кавычки
            val = val_raw.strip('"\'')

        return {key: val}

    msg = (
        f"Неподдерживаемый формат WHERE: '{where_input}'. "
        "Используйте формат key=value"
    )
    raise ValueError(msg)
