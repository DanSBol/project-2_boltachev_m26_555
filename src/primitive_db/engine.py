import re
from typing import Any, Callable, Dict, List, Optional

from .core import delete, insert, select, update
from .parser import parse_insert_row, parse_where_clause


def handle_create_table(args: List[str]) -> None:
    if len(args) < 3:
        error_msg = (
            "Ошибка: недостаточно аргументов. "
            "Пример: create_table users name:str age:int"
        )
        print(error_msg)
        return

    table_name = args[1]
    col_args = args[2:]

    metadata: Dict[str, str] = {}
    for c in col_args:
        if ":" not in c:
            err_fmt = f"Ошибка: неверный формат колонки '{c}'. Используйте col:type"
            print(err_fmt)
            return
        parts = c.split(":", 1)
        if len(parts) != 2:
            print(f"Ошибка: некорректный формат колонки '{c}'")
            return
        name, typ = parts
        metadata[name.strip()] = typ.strip()

    print(f"Таблица '{table_name}' создана со схемой: {metadata}")

def _map_values_to_row(values: List[Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {}
    for i, v in enumerate(values, start=1):
        col_name = f"col{i}"
        row[col_name] = v
    return row

def handle_insert(user_input: str) -> None:
    pattern = r"insert\s+into\s+(\w+)\s+values\s+(.*)"
    m = re.match(pattern, user_input, re.IGNORECASE)

    if not m:
        help_msg = (
            "Неверный формат INSERT. "
            "Пример: insert into users values (\"Alice\", 30)"
        )
        print(help_msg)
        return

    table_name, values_part = m.groups()

    try:
        values_list = parse_insert_row(values_part)
    except ValueError as e:
        print(f"Ошибка парсинга значений: {e}")
        return

    rows = [_map_values_to_row(values_list)]

    try:
        count = insert(table_name, rows)
        msg = (
            f"Запись успешно добавлена в таблицу '{table_name}'. "
            f"Добавлено строк: {count}"
        )
        print(msg)
    except Exception as e:
        err_msg = f"Ошибка INSERT: {e}"
        print(err_msg)

def handle_select(user_input: str) -> None:
    pattern = r"select\s+from\s+(\w+)(?:\s+where\s+(.*))?"
    m = re.match(pattern, user_input, re.IGNORECASE)

    if not m:
        help_msg = (
            "Неверный формат SELECT. "
            "Пример: select from users where name=Alice"
        )
        print(help_msg)
        return

    table_name, where_part = m.groups()
    where_dict = {}

    if where_part:
        try:
            where_dict = parse_where_clause(where_part)
        except ValueError as e:
            print(f"Ошибка WHERE: {e}")
            return

    data = select(table_name, where=where_dict)

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

def handle_update(user_input: str) -> None:
    pattern = (
        r"update\s+(\w+)\s+set\s+([^\s]+)\s*=\s*([^\s]+)"
        r"(?:\s+where\s+(.*))?"
    )
    m = re.match(pattern, user_input, re.IGNORECASE)

    if not m:
        help_msg = (
            "Неверный формат UPDATE. "
            "Пример: update users set age = 29 where name = \"Sergei\""
        )
        print(help_msg)
        return

    table_name, col, val_raw, where_part = m.groups()

    val = val_raw.strip('"\'')
    try:
        if "." in val:
            val = float(val)
        else:
            val = int(val)
    except ValueError:
        pass  # оставляем строкой

    where_dict = {}
    if where_part:
        try:
            where_dict = parse_where_clause(where_part)
        except ValueError as e:
            print(f"Ошибка WHERE: {e}")
            return

    set_data = {col: val}
    updated_count = update(table_name, set_data=set_data, where=where_dict)
    print(f"Обновлено строк: {updated_count}")

def handle_delete(user_input: str) -> None:
    pattern = r"delete\s+from\s+(\w+)\s+where\s+(.*)"
    m = re.match(pattern, user_input, re.IGNORECASE)

    if not m:
        help_msg = (
            "Неверный формат DELETE. "
            "Пример: delete from users where name=Bob"
        )
        print(help_msg)
        return

    table_name, where_part = m.groups()

    try:
        where_dict = parse_where_clause(where_part)
    except ValueError as e:
        print(f"Ошибка WHERE: {e}")
        return

    deleted_count = delete(table_name, where=where_dict)
    print(f"Удалено строк: {deleted_count}")

def show_help() -> None:
    print("Доступные команды:")
    print("  create_table <имя> <col:type> ...      - создать таблицу")
    print("  insert into <имя> values (...)         - вставить строку")
    print("  select from <имя> [where key=value]   - выбрать данные")
    print("  update <имя> set col=value [where...]  - обновить данные")
    print("  delete from <имя> where key=value      - удалить данные")
    print("  list_tables                            - показать список таблиц")
    print("  quit                                   - выйти")

COMMAND_HANDLERS: Dict[str, Callable[[str], None]] = {
    "create_table": lambda cmd: handle_create_table(cmd.split()),
    "insert": handle_insert,
    "select": handle_select,
    "update": handle_update,
    "delete": handle_delete,
}

def run() -> None:
    print("Primitive DB Engine запущен. Введите 'help' для списка команд.")

    while True:
        try:
            user_input = input("> ").strip()
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
            print("[INFO] Список таблиц: users, orders, products (из файловой системы)")
            continue

        handler: Optional[Callable[[str], None]] = None
        for prefix, func in COMMAND_HANDLERS.items():
            if user_input.startswith(prefix):
                handler = func
                break

        if handler is not None:
            handler(user_input)
        else:
            print("Неизвестная команда. Введите 'help'.")