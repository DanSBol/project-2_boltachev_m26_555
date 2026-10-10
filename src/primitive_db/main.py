import argparse
from typing import Any, Dict, List

from prettytable import PrettyTable

from .core import delete, drop_table, get_table_stats, insert, select, update


def print_table(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("(пусто)")
        return

    table = PrettyTable()
    headers = rows[0].keys()
    table.field_names = headers
    for row in rows:
        table.add_row([row.get(h) for h in headers])
    print(table)


def parse_where(where_str: str) -> Dict[str, Any]:
    result = {}
    if not where_str:
        return result

    pairs = where_str.split(",")
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v_raw = pair.split("=", 1)
        key = k.strip()
        v_str = v_raw.strip()

        # Сначала пробуем превратить в число
        val = v_str
        if v_str.lstrip("-").isdigit():
            val = int(v_str)
        else:
            clean = v_str.replace(".", "", 1).lstrip("-")
            if v_str.count(".") == 1 and clean.isdigit():
                val = float(v_str)

        result[key] = val

    return result

def handle_select(args: argparse.Namespace) -> None:
    where = parse_where(args.where) if args.where else None
    rows = select(args.table, where)
    print_table(rows)


def handle_insert(args: argparse.Namespace) -> None:
    if not args.values:
        print("Ошибка: --values обязателен для insert")
        return

    row: Dict[str, Any] = {}
    for pair in args.values:
        if "=" not in pair:
            continue
        k, v_raw = pair.split("=", 1)
        key = k.strip()
        v_str = v_raw.strip()

        # Сначала пробуем превратить в число, потом присваиваем
        val = v_str
        if v_str.lstrip("-").isdigit():
            val = int(v_str)
        else:
            # Проверка на float: ровно одна точка, остальное — цифры (с учётом минуса)
            clean = v_str.replace(".", "", 1).lstrip("-")
            if v_str.count(".") == 1 and clean.isdigit():
                val = float(v_str)

        row[key] = val

    count = insert(args.table, [row])
    print(f"Добавлено строк: {count}")

def handle_delete(args: argparse.Namespace) -> None:
    where = parse_where(args.where)
    count = delete(args.table, where)
    if count is not None:
        print(f"Удалено строк: {count}")

def handle_drop(args: argparse.Namespace) -> None:
    ok = drop_table(args.table)
    if ok:
        print(f"Таблица '{args.table}' удалена.")
    else:
        print(f"Таблица '{args.table}' не найдена.")

def handle_update(args: argparse.Namespace) -> None:
    set_clause = parse_where(args.set)
    where = parse_where(args.where)
    count = update(args.table, set_clause, where)
    print(f"Обновлено строк: {count}")

def handle_stats(args: argparse.Namespace) -> None:
    stats_data = get_table_stats(args.table)
    print(f"Таблица: {stats_data['table']}")
    print(f"Строк: {stats_data['row_count']}")
    print(f"Колонки: {', '.join(stats_data['columns'])}")
    if stats_data["sample_row"]:
        print("Пример строки:")
        print_table([stats_data["sample_row"]])

def main() -> None:
    help_desc = "CLI для примитивной JSON-БД"

    help_select = "Выбрать строки из таблицы"
    help_insert = "Вставить строки в таблицу"
    help_delete = "Удалить строки из таблицы"
    help_drop = "Полностью удалить таблицу (файл)"
    help_update = "Обновить строки в таблице"
    help_stats = "Статистика по таблице"

    help_table = "Имя таблицы"
    help_where = "Условия в формате key=value,key2=value2"
    help_values = (
        "Пары field=value для каждой строки "
        "(через пробел)"
    )
    help_set = (
        "Новые значения: field=value,field2=value2"
    )
    help_where_required = (
        "Условия удаления (обязательно)"
    )

    parser = argparse.ArgumentParser(description=help_desc)
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # select
    sel = subparsers.add_parser("select", help=help_select)
    sel.add_argument("table", help=help_table)
    sel.add_argument("--where", help=help_where)

    # insert
    ins = subparsers.add_parser("insert", help=help_insert)
    ins.add_argument("table", help=help_table)
    ins.add_argument("--values", nargs="+", help=help_values)

    # delete
    dlt = subparsers.add_parser("delete", help=help_delete)
    dlt.add_argument("table", help=help_table)
    dlt.add_argument("--where", required=True, help=help_where_required)

    # drop_table
    drop = subparsers.add_parser("drop", help=help_drop)
    drop.add_argument("table", help=help_table)

    # update
    upd = subparsers.add_parser("update", help=help_update)
    upd.add_argument("table", help=help_table)
    upd.add_argument("--set", required=True, help=help_set)
    upd.add_argument("--where", required=True, help=help_where)

    # stats
    stats = subparsers.add_parser("stats", help=help_stats)
    stats.add_argument("table", help=help_table)

    args = parser.parse_args()

    if args.command == "select":
        handle_select(args)
    elif args.command == "insert":
        handle_insert(args)
    elif args.command == "delete":
        handle_delete(args)
    elif args.command == "drop":
        handle_drop(args)
    elif args.command == "update":
        handle_update(args)
    elif args.command == "stats":
        handle_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
