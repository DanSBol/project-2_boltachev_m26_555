# src/primitive_db/engine.py
from .core import delete, insert, select, update
from .parser import parse_insert_row, parse_where_clause


def handle_create_table(args):
    if len(args) < 3:
        error_msg = (
            "Ошибка: недостаточно аргументов. "
            "Пример: create_table users name:str age:int"
        )
        print(error_msg)
        return

    table_name = args[1]
    col_args = args[2:]

    metadata = {}
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

def _map_values_to_row(values):
    row = {}
    for i, v in enumerate(values, start=1):
        col_name = f"col{i}"
        row[col_name] = v
    return row

def _parse_insert(user_input):
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

def _parse_select(user_input):
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

def handle_update(user_input):
    table_name, col, val_raw, where_part = _parse_update(user_input)
    if table_name is None:
        help_msg = (
            "Неверный формат UPDATE. "
            "Пример: update users set age = 44 where name = \"Dan\""
        )
        print(help_msg)
        return

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

def _parse_delete(user_input):
    lower = user_input.lower()
    if not lower.startswith("delete from"):
        return None, None

    marker = "delete from"
    rest = user_input[len(marker):].strip()

    where_marker = "where"
    where_idx = rest.lower().find(where_marker)
    if where_idx == -1:
        # По нашей спецификации where обязателен
        return None, None

    table_part = rest[:where_idx].strip()
    where_part = rest[where_idx + len(where_marker):].strip()

    table_name = table_part.split()[0] if table_part else ""
    if not table_name:
        return None, None

    return table_name, where_part

def handle_delete(user_input):
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
    print(f"Удалено строк: {deleted_count}")

def show_help():
    print("Доступные команды:")
    print("  create_table <имя> <col:type> ...      - создать таблицу")
    print("  insert into <имя> values (...)         - вставить строку")
    print("  select from <имя> [where key=value]   - выбрать данные")
    print("  update <имя> set col=value [where...]  - обновить данные")
    print("  delete from <имя> where key=value      - удалить данные")
    print("  list_tables                            - показать список таблиц")
    print("  quit                                   - выйти")

COMMAND_HANDLERS = {
    "create_table": lambda cmd: handle_create_table(cmd.split()),
    "insert": handle_insert,
    "select": handle_select,
    "update": handle_update,
    "delete": handle_delete,
}

def run():
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

        handler = None
        for prefix, func in COMMAND_HANDLERS.items():
            if user_input.startswith(prefix):
                handler = func
                break

        if handler is not None:
            handler(user_input)
        else:
            print("Неизвестная команда. Введите 'help'.")