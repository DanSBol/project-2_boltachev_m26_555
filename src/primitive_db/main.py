import argparse
from typing import List, Dict, Any
from prettytable import PrettyTable

from .core import insert, select, delete, drop_table, update, get_table_stats


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
    """
    Парсит where в формате key=value,key2=value2
    Пример: age=25,name=Alice
    """
    result = {}
    if not where_str:
        return result
    pairs = where_str.split(",")
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        # Простая эвристика: если v число — делаем int
        if v.isdigit():
            v = int(v)
        result[k.strip()] = v.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI для примитивной JSON-БД")
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # select
    sel = subparsers.add_parser("select", help="Выбрать строки из таблицы")
    sel.add_argument("table", help="Имя таблицы")
    sel.add_argument("--where", help="Условия в формате key=value,key2=value2")

    # insert
    ins = subparsers.add_parser("insert", help="Вставить строки в таблицу")
    ins.add_argument("table", help="Имя таблицы")
    ins.add_argument("--values", nargs="+", help="Пары field=value для каждой строки (через пробел)")

    # delete
    dlt = subparsers.add_parser("delete", help="Удалить строки из таблицы")
    dlt.add_argument("table", help="Имя таблицы")
    dlt.add_argument("--where", required=True, help="Условия удаления (обязательно)")

    # drop_table
    drop = subparsers.add_parser("drop", help="Полностью удалить таблицу (файл)")
    drop.add_argument("table", help="Имя таблицы")

    # update
    upd = subparsers.add_parser("update", help="Обновить строки в таблице")
    upd.add_argument("table", help="Имя таблицы")
    upd.add_argument("--set", required=True, help="Новые значения: field=value,field2=value2")
    upd.add_argument("--where", required=True, help="Условие обновления: key=value")

    # stats
    stats = subparsers.add_parser("stats", help="Статистика по таблице")
    stats.add_argument("table", help="Имя таблицы")

    args = parser.parse_args()

    if args.command == "select":
        where = parse_where(args.where) if args.where else None
        rows = select(args.table, where)
        print_table(rows)

    elif args.command == "insert":
        # Простой парсинг: каждая пара field=value становится полем строки
        # Формат вызова: --values name=Alice age=30 name=Bob age=25
        if not args.values:
            print("Ошибка: --values обязателен для insert")
            return
        # Группируем пары по строкам (каждые N пар — одна строка; здесь упрощаем: все пары — одна строка)
        row: Dict[str, Any] = {}
        for pair in args.values:
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            if v.isdigit():
                v = int(v)
            row[k.strip()] = v.strip()
        count = insert(args.table, [row])
        print(f"Добавлено строк: {count}")

    elif args.command == "delete":
        where = parse_where(args.where)
        count = delete(args.table, where)
        if count is not None:
            print(f"Удалено строк: {count}")

    elif args.command == "drop":
        ok = drop_table(args.table)
        if ok:
            print(f"Таблица '{args.table}' удалена.")
        else:
            print(f"Таблица '{args.table}' не найдена.")

    elif args.command == "update":
        set_clause = parse_where(args.set)
        where = parse_where(args.where)
        count = update(args.table, set_clause, where)
        print(f"Обновлено строк: {count}")

    elif args.command == "stats":
        stats_data = get_table_stats(args.table)
        print(f"Таблица: {stats_data['table']}")
        print(f"Строк: {stats_data['row_count']}")
        print(f"Колонки: {', '.join(stats_data['columns'])}")
        if stats_data["sample_row"]:
            print("Пример строки:")
            print_table([stats_data["sample_row"]])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
