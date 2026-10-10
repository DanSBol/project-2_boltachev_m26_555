"""Интерактивный режим: цикл ввода и обработка SQL-подобных команд."""

import os
import shlex

from prompt import prompt

from .constants import DATA_DIR, ID_COLUMN, METADATA_FILE, VALID_TYPES
from .core import delete, insert, select, update
from .parser import parse_insert_row, parse_where_clause
from .utils import ensure_data_dir, load_metadata, save_metadata


def handle_create_table(args):
    """Создаёт таблицу: добавляет колонку id и сохраняет схему в метаданные."""
    if len(args) < 3:
        error_msg = (
            "Ошибка: недостаточно аргументов. "
            "Пример: create_table users name:str age:int"
        )
        print(error_msg)
        return

    table_name = args[1]

    # Колонка id добавляется в схему автоматически
    schema = {ID_COLUMN: "int"}
    for col_spec in args[2:]:
        if ":" not in col_spec:
            err_fmt = (
                f"Ошибка: неверный формат колонки '{col_spec}'. "
                "Используйте col:type"
            )
            print(err_fmt)
            return

        name, typ = col_spec.split(":", 1)
        name = name.strip()
        typ = typ.strip().lower()
        if typ not in VALID_TYPES:
            allowed = ", ".join(VALID_TYPES)
            print(f"Ошибка: неизвестный тип '{typ}'. Допустимые типы: {allowed}")
            return
        if name in schema:
            print(f"Ошибка: колонка '{name}' уже объявлена.")
            return
        schema[name] = typ

    ensure_data_dir()
    metadata = load_metadata()
    if table_name in metadata:
        print(f"Ошибка: таблица '{table_name}' уже существует.")
        return
    metadata[table_name] = schema
    save_metadata(METADATA_FILE, metadata)
    print(f"Таблица '{table_name}' создана со схемой: {schema}")


def _map_values_to_row(values):
    """Сопоставляет значения колонкам col1..colN по порядку."""
    row = {}
    for i, v in enumerate(values, start=1):
        row[f"col{i}"] = v
    return row


def _validate_row_against_schema(table_name, row):
    """Проверяет значения строки против схемы таблицы. Возвращает True при успехе."""
    metadata = load_metadata()
    schema = metadata.get(table_name, {})
    if not schema:
        print(f"Ошибка: таблица '{table_name}' не найдена в метаданных. "
              "Создайте её командой create_table.")
        return False

    for key, value in row.items():
        if key == ID_COLUMN:
            continue
        expected = schema.get(key)
        if expected is None:
            print(f"Ошибка: колонка '{key}' не объявлена в схеме таблицы.")
            return False
        if expected == "int" and not isinstance(value, int):
            print(f"Ошибка: значение поля '{key}' должно быть int.")
            return False
        if expected == "float" and not isinstance(value, (int, float)):
            print(f"Ошибка: значение поля '{key}' должно быть float.")
            return False
        if expected == "str" and not isinstance(value, str):
            print(f"Ошибка: значение поля '{key}' должно быть строкой.")
            return False
        if expected == "bool" and not isinstance(value, bool):
            print(f"Ошибка: значение поля '{key}' должно быть bool.")
            return False

    return True


def _parse_insert(user_input):
    """Разбирает 'insert into <table> values <...>'; возвращает (таблица, значения)."""
    lower = user_input.lower()
    if not lower.startswith("insert into"):
        return None, None

    values_marker = "values"
    idx = lower.find(values_marker)
    if idx == -1:
        return None, None

    before = user_input[:idx].strip()
    after = user_input[idx + len(values_marker):].strip()

    prefix = "insert into"
    if not before.lower().startswith(prefix):
        return None, None
    table_part = before[len(prefix):].strip()
    table_name = table_part.split()[0] if table_part else ""
    if not table_name:
        return None, None

    return table_name, after


def handle_insert(user_input):
    """Обрабатывает команду insert into с валидацией типов по схеме."""
    table_name, values_part = _parse_insert(user_input)
    if table_name is None:
        help_msg = (
            "Неверный формат INSERT. "
            "Пример: insert into users values (\"Tatyana\", 43)"
        )
        print(help_msg)
        return

    try:
        values_list = parse_insert_row(values_part)
    except ValueError as e:
        print(f"Ошибка парсинга значений: {e}")
        return

    rows = [_map_values_to_row(values_list)]
    if not _validate_row_against_schema(table_name, rows[0]):
        return

    count = insert(table_name, rows)
    if count is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    msg = (
        f"Запись успешно добавлена в таблицу '{table_name}'. "
        f"Добавлено строк: {count}"
    )
    print(msg)


def _parse_select(user_input):
    """Разбирает 'select from <table> [where ...]'; возвращает (таблица, where)."""
    lower = user_input.lower()
    if not lower.startswith("select from"):
        return None, None

    marker = "select from"
    rest = user_input[len(marker):].strip()

    parts = rest.split("where", 1)  # максимум 2 части
    table_part = parts[0].strip()
    where_part = parts[1].strip() if len(parts) > 1 else None

    table_name = table_part.split()[0] if table_part else ""
    if not table_name:
        return None, None

    return table_name, where_part


def handle_select(user_input):
    """Обрабатывает команду select from и печатает результат."""
    table_name, where_part = _parse_select(user_input)
    if table_name is None:
        help_msg = (
            "Неверный формат SELECT. "
            "Пример: select from users where name=Tatyana"
        )
        print(help_msg)
        return

    where_dict = {}
    if where_part:
        try:
            where_dict = parse_where_clause(where_part)
        except ValueError as e:
            print(f"Ошибка WHERE: {e}")
            return

    data = select(table_name, where=where_dict)
    if data is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return

    if not data:
        print("Данные не найдены.")
        return

    headers = list(data[0].keys())
    header_line = " | ".join(headers)
    separator = "-" * len(header_line)

    print(header_line)
    print(separator)
    for row in data:
        line = " | ".join(str(row.get(h, "")) for h in headers)
        print(line)


def _parse_update(user_input):
    """Разбирает 'update <table> set col=value [where ...]'."""
    lower = user_input.lower()
    if not lower.startswith("update"):
        return None, None, None, None

    set_marker = "set"
    set_idx = lower.find(set_marker, 6)  # ищем после 'update'
    if set_idx == -1:
        return None, None, None, None

    table_part = user_input[6:set_idx].strip()
    table_name = table_part.split()[0] if table_part else ""
    if not table_name:
        return None, None, None, None

    set_rest = user_input[set_idx + len(set_marker):].strip()

    where_marker = "where"
    where_idx = set_rest.lower().find(where_marker)
    if where_idx != -1:
        set_clause = set_rest[:where_idx].strip()
        where_part = set_rest[where_idx + len(where_marker):].strip()
    else:
        set_clause = set_rest
        where_part = None

    if "=" not in set_clause:
        return None, None, None, None

    equal_idx = set_clause.find("=")
    col = set_clause[:equal_idx].strip()
    val_raw = set_clause[equal_idx + 1:].strip()

    if not col or not val_raw:
        return None, None, None, None

    return table_name, col, val_raw, where_part


def _convert_value(val_raw):
    """Пытается привести строку к int/float, иначе оставляет строкой."""
    val = val_raw.strip('"\'')
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def handle_update(user_input):
    """Обрабатывает команду update."""
    table_name, col, val_raw, where_part = _parse_update(user_input)
    if table_name is None:
        help_msg = (
            "Неверный формат UPDATE. "
            "Пример: update users set age = 44 where name = \"Dan\""
        )
        print(help_msg)
        return

    val = _convert_value(val_raw)

    where_dict = {}
    if where_part:
        try:
            where_dict = parse_where_clause(where_part)
        except ValueError as e:
            print(f"Ошибка WHERE: {e}")
            return
    if not where_dict:
        print("Ошибка: для update требуется непустое условие where.")
        return

    set_data = {col: val}
    updated_count = update(table_name, set_data, where_dict)
    if updated_count is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    print(f"Обновлено строк: {updated_count}")


def _parse_delete(user_input):
    """Разбирает 'delete from <table> where ...'; where обязателен."""
    lower = user_input.lower()
    if not lower.startswith("delete from"):
        return None, None

    marker = "delete from"
    rest = user_input[len(marker):].strip()

    where_marker = "where"
    where_idx = rest.lower().find(where_marker)
    if where_idx == -1:
        # По спецификации where обязателен
        return None, None

    table_part = rest[:where_idx].strip()
    where_part = rest[where_idx + len(where_marker):].strip()

    table_name = table_part.split()[0] if table_part else ""
    if not table_name:
        return None, None

    return table_name, where_part


def handle_delete(user_input):
    """Обрабатывает команду delete from."""
    table_name, where_part = _parse_delete(user_input)
    if table_name is None:
        help_msg = (
            "Неверный формат DELETE. "
            "Пример: delete from users where name=Bob"
        )
        print(help_msg)
        return

    try:
        where_dict = parse_where_clause(where_part)
    except ValueError as e:
        print(f"Ошибка WHERE: {e}")
        return

    deleted_count = delete(table_name, where=where_dict)
    if deleted_count is None:
        # Операция отменена пользователем либо ошибка напечатана декоратором
        return
    print(f"Удалено строк: {deleted_count}")


def list_tables():
    """Выводит список таблиц (JSON-файлов в директории данных)."""
    if not os.path.exists(DATA_DIR):
        print("Таблиц нет.")
        return
    tables = [f[:-5] for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    if tables:
        print("Список таблиц: " + ", ".join(sorted(tables)))
    else:
        print("Таблиц нет.")


def show_help():
    """Выводит справку по интерактивным командам."""
    print("Доступные команды:")
    print("  create_table <имя> <col:type> ...      - создать таблицу")
    print("  insert into <имя> values (...)         - вставить строку")
    print("  select from <имя> [where key=value]   - выбрать данные")
    print("  update <имя> set col=value [where...]  - обновить данные")
    print("  delete from <имя> where key=value      - удалить данные")
    print("  list_tables                            - показать список таблиц")
    print("  quit                                   - выйти")


def handle_create_command(user_input):
    """Разбирает команду create_table с учётом кавычек через shlex."""
    try:
        args = shlex.split(user_input)
    except ValueError as e:
        print(f"Ошибка разбора команды: {e}")
        return
    handle_create_table(args)


COMMAND_HANDLERS = {
    "create_table": handle_create_command,
    "insert": handle_insert,
    "select": handle_select,
    "update": handle_update,
    "delete": handle_delete,
}


def run():
    """Основной цикл интерактивного режима."""
    print("Primitive DB Engine запущен. Введите 'help' для списка команд.")

    while True:
        try:
            user_input = prompt("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из системы.")
            break

        if not user_input:
            continue

        cmd_lower = user_input.lower()

        if cmd_lower in ("quit", "exit"):
            print("До свидания!")
            break
        elif cmd_lower == "help":
            show_help()
            continue
        elif cmd_lower == "list_tables":
            list_tables()
            continue

        handler = None
        for prefix, func in COMMAND_HANDLERS.items():
            if user_input.startswith(prefix):
                handler = func
                break

        if handler is not None:
            handler(user_input)
        else:
            print("Неизвестная команда. Введите 'help'.")


if __name__ == "__main__":
    run()
