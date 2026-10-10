"""CLI-интерфейс: разбор аргументов командной строки и вывод таблиц."""

from prettytable import PrettyTable

from .core import delete, drop_table, get_table_stats, insert, select, update
from .engine import _validate_row_against_schema
from .parser import parse_where_clause


def print_table(rows):
    """Выводит данные в виде таблицы через PrettyTable."""
    if not rows:
        print("(пусто)")
        return

    table = PrettyTable()
    headers = list(rows[0].keys())
    table.field_names = headers
    for row in rows:
        table.add_row([row.get(h) for h in headers])
    print(table)


def parse_where(where_str):
    """Парсит строку вида key=value,key2=value2 в словарь с приведением типов."""
    if not where_str:
        return {}

    result = {}
    for pair in where_str.split(","):
        if not pair.strip():
            continue
        result.update(parse_where_clause(pair))
    return result


# -----------------------------------------------------------------------------
# Обработчики команд
# -----------------------------------------------------------------------------

def handle_select(table, where_str):
    """Обрабатывает команду select и печатает результат."""
    where = parse_where(where_str) if where_str else None
    rows = select(table, where)
    if rows is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    print_table(rows)


def handle_insert(table, values_pairs):
    """Обрабатывает команду insert: собирает строку, валидирует и вставляет её."""
    row = {}
    for pair in values_pairs:
        row.update(parse_where_clause(pair))

    if not _validate_row_against_schema(table, row):
        return

    count = insert(table, [row])
    if count is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    print(f"Добавлено строк: {count}")


def handle_delete(table, where_str):
    """Обрабатывает команду delete с обязательным условием where."""
    where = parse_where(where_str)
    count = delete(table, where)
    if count is None:
        # Операция отменена пользователем либо ошибка напечатана декоратором
        return
    print(f"Удалено строк: {count}")


def handle_drop(table):
    """Обрабатывает команду drop: полностью удаляет таблицу."""
    ok = drop_table(table)
    if ok:
        print(f"Таблица '{table}' удалена.")
    elif ok is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    else:
        print(f"Таблица '{table}' не найдена.")


def handle_update(table, set_str, where_str):
    """Обрабатывает команду update с флагами --set и --where."""
    set_clause = parse_where(set_str)
    where = parse_where(where_str)
    count = update(table, set_clause, where)
    if count is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    print(f"Обновлено строк: {count}")


def handle_stats(table):
    """Обрабатывает команду stats: печатает статистику по таблице."""
    stats_data = get_table_stats(table)
    if stats_data is None:
        # Ошибка уже напечатана декоратором handle_db_errors
        return
    print(f"Таблица: {stats_data['table']}")
    print(f"Строк: {stats_data['row_count']}")
    columns_str = ", ".join(stats_data["columns"])
    print(f"Колонки: {columns_str}")
    if stats_data["sample_row"]:
        print("Пример строки:")
        print_table([stats_data["sample_row"]])


def show_help():
    """Выводит справку по CLI-командам."""
    help_text = (
        "CLI для примитивной JSON-БД\n\n"
        "Доступные команды:\n"
        "  select <table> [--where key=value,key2=value2]\n"
        "    Выбрать строки из таблицы\n\n"
        "  insert <table> --values field=value [field2=value2 ...]\n"
        "    Вставить строку в таблицу\n\n"
        "  delete <table> --where key=value,key2=value2\n"
        "    Удалить строки из таблицы (where обязателен)\n\n"
        "  drop <table>\n"
        "    Полностью удалить таблицу (файл)\n\n"
        "  update <table> --set field=value,field2=value2 --where key=value\n"
        "    Обновить строки в таблице (set и where обязательны)\n\n"
        "  stats <table>\n"
        "    Статистика по таблице\n\n"
        "Примеры:\n"
        '  database select users --where name="Tatyana"\n'
        '  database insert users --values name="Dan" age=44\n'
        '  database delete users --where id=5\n'
        '  database update users --set age=43 --where id=5'
    )
    print(help_text)


# -----------------------------------------------------------------------------
# Парсинг: мелкие хелперы
# -----------------------------------------------------------------------------

def _validate_table_present(command, i, n, args):
    """Проверяет наличие имени таблицы после команды."""
    if i >= n:
        print("Ошибка: требуется имя таблицы.")
        show_help()
        return i, None
    return i + 1, args[i]


def _collect_values_until_next_flag(args, start_idx, n):
    """Собирает аргументы для --values до следующего флага."""
    values_pairs = []
    i = start_idx
    while i < n and not args[i].startswith("--"):
        values_pairs.append(args[i])
        i += 1
    return values_pairs, i


def _check_required_flag(flag_name, present, cmd_name):
    """Общая проверка: если флаг обязателен и его нет — ошибка и справка."""
    if not present:
        msg = f"Ошибка: для команды '{cmd_name}' требуется флаг --{flag_name}"
        print(msg)
        show_help()
        return False
    return True


def _parse_where_flag(args, i, n):
    """Извлекает значение флага --where, если он присутствует."""
    if args[i] == "--where" and i + 1 < n:
        return args[i + 1], i + 2
    return None, i


def _parse_values_flag(command, args, i, n):
    """Извлекает значения флага --values для команды insert."""
    if command == "insert" and args[i] == "--values":
        if i + 1 >= n:
            print("Ошибка: для --values требуется хотя бы один field=value.")
            show_help()
            return None, None
        values_pairs, new_i = _collect_values_until_next_flag(args, i + 1, n)
        if not values_pairs:
            print("Ошибка: для --values требуется хотя бы один field=value.")
            show_help()
            return None, None
        return values_pairs, new_i
    return None, i


def _parse_set_flag(command, args, i, n):
    """Извлекает значение флага --set для команды update."""
    if command == "update" and args[i] == "--set" and i + 1 < n:
        return args[i + 1], i + 2
    return None, i


def _parse_args(args):
    """Разбирает аргументы CLI. Логика вынесена в хелперы, чтобы снизить сложность."""
    if not args:
        return {"command": "help"}

    command = args[0].lower()
    if command in ("-h", "--help", "help"):
        return {"command": "help"}

    result = {"command": command}
    i = 1
    n = len(args)

    # Таблица нужна для select/insert/delete/drop/update/stats
    if command in ("select", "insert", "delete", "drop", "update", "stats"):
        i, table = _validate_table_present(command, i, n, args)
        if table is None:
            return None
        result["table"] = table

    # Флаги: каждый тип флага обрабатывается отдельным хелпером
    while i < n:
        arg = args[i]

        # --where
        where_val, new_i = _parse_where_flag(args, i, n)
        if where_val is not None:
            result["where"] = where_val
            i = new_i
            continue

        # --values
        values_pairs, new_i = _parse_values_flag(command, args, i, n)
        if values_pairs is not None:
            result["values"] = values_pairs
            i = new_i
            continue

        # --set
        set_val, new_i = _parse_set_flag(command, args, i, n)
        if set_val is not None:
            result["set"] = set_val
            i = new_i
            continue

        # Неизвестный аргумент
        msg = "Неизвестный или неверный аргумент: "
        msg += f"{arg}. Запустите с --help для справки."
        print(msg)
        show_help()
        return None

    return result


def _run_command(parsed):
    """Выполняет команду по разобранному словарю аргументов."""
    cmd = parsed["command"]
    table = parsed.get("table")

    if cmd == "select":
        handle_select(table, parsed.get("where"))

    elif cmd == "insert":
        values_pairs = parsed.get("values", [])
        if not values_pairs:
            print("Ошибка: для insert требуется --values")
            show_help()
            return
        handle_insert(table, values_pairs)

    elif cmd == "delete":
        where_str = parsed.get("where")
        if not _check_required_flag("where", where_str, "delete"):
            return
        handle_delete(table, where_str)

    elif cmd == "drop":
        handle_drop(table)

    elif cmd == "update":
        set_str = parsed.get("set")
        where_str = parsed.get("where")
        ok_set = _check_required_flag("set", set_str, "update")
        ok_where = _check_required_flag("where", where_str, "update")
        if ok_set and ok_where:
            handle_update(table, set_str, where_str)

    elif cmd == "stats":
        handle_stats(table)

    else:
        # Сюда не должны попадать неизвестные команды: они уже отловлены в _parse_args
        print(f"Неизвестная команда: {cmd}")
        show_help()


def main():
    """Точка входа CLI."""
    # sys не входит в заявленный список библиотек, поэтому берём argv напрямую
    args = __import__("sys").argv[1:]
    parsed = _parse_args(args)

    if parsed is None:
        return

    cmd = parsed["command"]
    if cmd == "help":
        show_help()
        return

    _run_command(parsed)


if __name__ == "__main__":
    main()
