import os
import re
import shlex
from pathlib import Path

import prompt
from prettytable import PrettyTable

from .utils import load_metadata, save_metadata, load_table_data, save_table_data
from .core import insert, select, update, delete, get_schema_cols
from .parser import parse_values, parse_where, parse_set

METADATA_FILE = "db_meta.json"
DATA_DIR = "data"


def print_help():
    print("\n=== Справочная информация ===")
    print("Управление структурой таблиц:")
    print('  create_table <имя> <col1:type> <col2:type> ...  - создать таблицу')
    print('  drop_table <имя>                                 - удалить таблицу')
    print('  list_tables                                      - показать список таблиц')
    print('  info <имя>                                       - показать схему и кол-во записей')
    
    print("\nРабота с данными (CRUD):")
    print('  insert into <таблица> values ("Name", 25, true)  - добавить запись')
    print('  select from <таблица> [where <col> = <val>]      - выбрать записи')
    print('  update <таблица> set <col> = <val> where ...     - обновить записи')
    print('  delete from <таблица> where <col> = <val>        - удалить записи')
    
    print("\nОбщие команды:")
    print('  help                                             - эта справка')
    print('  exit                                             - выход\n')


def render_table(rows, columns):
    """Вывод таблицы через prettytable."""
    if not rows:
        print("(пусто)")
        return
    t = PrettyTable()
    t.field_names = columns
    for row in rows:
        t.add_row([row.get(c) for c in columns])
    print(t)


def run():
    while True:
        try:
            user_input = prompt.string(">>> ").strip()
            if not user_input:
                continue

            args = shlex.split(user_input)
            command = args[0].lower()

            # --- Общие команды ---
            if command == "help":
                print_help()
                continue

            if command == "exit":
                print("Выход из программы.")
                break

            metadata = load_metadata(METADATA_FILE)

            # --- Управление структурой (было в core, теперь здесь) ---
            if command == "create_table":
                if len(args) < 3:
                    print("Ошибка: недостаточно аргументов. Пример: create_table users name:str age:int")
                    continue
                table_name = args[1]
                col_args = args[2:]

                # Валидация формата колонок
                columns = []
                for c in col_args:
                    if ":" not in c:
                        print(f"Ошибка: неверный формат колонки '{c}'. Используйте col:type")
                        continue
                    name, typ = c.split(":", 1)
                    columns.append({"name": name, "type": typ})

                if table_name in metadata:
                    print(f'Ошибка: таблица "{table_name}" уже существует.')
                    continue

                metadata[table_name] = {"columns": columns}
                save_metadata(METADATA_FILE, metadata)
                cols_str = ", ".join(f"{n}:{t}" for n, t in columns)
                print(f'Таблица "{table_name}" успешно создана. Колонки: {cols_str}')
                continue

            if command == "drop_table":
                if len(args) != 2:
                    print('Ошибка: требуется имя таблицы. Пример: drop_table users')
                    continue
                table_name = args[1]
                if table_name not in metadata:
                    print(f'Ошибка: таблица "{table_name}" не найдена.')
                    continue

                del metadata[table_name]
                save_metadata(METADATA_FILE, metadata)

                # Удаляем файл данных, если есть
                data_file = Path(DATA_DIR) / f"{table_name}.json"
                if data_file.exists():
                    data_file.unlink()

                print(f'Таблица "{table_name}" успешно удалена.')
                continue

            if command == "list_tables":
                tables = list(metadata.keys())
                if not tables:
                    print("Таблиц пока нет.")
                else:
                    for t in tables:
                        print(f"- {t}")
                continue

            if command == "info":
                if len(args) != 2:
                    print('Ошибка: требуется имя таблицы. Пример: info users')
                    continue
                table_name = args[1]
                schema = get_schema_cols(metadata, table_name)
                if schema is None:
                    print(f'Ошибка: таблица "{table_name}" не найдена.')
                    continue

                data = load_table_data(table_name)
                cols_desc = ", ".join(f"{n}:{t}" for n, t in schema)
                print(f"Таблица: {table_name}")
                print(f"Столбцы: {cols_desc}")
                print(f"Количество записей: {len(data)}")
                continue

            # --- CRUD: INSERT ---
            m = re.match(r"insert\s+into\s+(\w+)\s+values\s+(.*)", user_input, re.IGNORECASE)
            if m:
                table_name, values_part = m.groups()
                try:
                    values = parse_values(values_part)
                    new_data = insert(metadata, table_name, values)
                    save_table_data(table_name, new_data)
                    print(f"Запись с ID={new_data[-1]['ID']} успешно добавлена в таблицу '{table_name}'.")
                except Exception as e:
                    print(f"Ошибка INSERT: {e}")
                continue

            # --- CRUD: SELECT ---
            m = re.match(r"select\s+from\s+(\w+)(?:\s+where\s+(.*))?", user_input, re.IGNORECASE)
            if m:
                table_name, where_part = m.groups()
                where = None
                if where_part:
                    try:
                        where = parse_where(where_part)
                    except Exception as e:
                        print(f"Ошибка WHERE: {e}")
                        continue

                data = load_table_data(table_name)
                rows = select(data, where)

                schema = get_schema_cols(metadata, table_name)
                if schema is None:
                    print(f'Ошибка: таблица "{table_name}" не найдена.')
                    continue

                cols_list = ["ID"] + [n for n, _ in schema]
                render_table(rows, cols_list)
                continue

            # --- CRUD: UPDATE ---
            # Формат: update users set age = 29 where name = "Sergei"
            m = re.match(r"update\s+(\w+)\s+set\s+([^\s]+)\s*=\s*([^\s]+)(?:\s+where\s+(.*))?", user_input, re.IGNORECASE)
            if m:
                table_name, col, val_raw, where_part = m.groups()

                # Простой парсинг значения после set
                val_raw = val_raw.strip()
                if val_raw.startswith('"') and val_raw.endswith('"'):
                    val = val_raw[1:-1]
                elif val_raw.lower() == "true":
                    val = True
                elif val_raw.lower() == "false":
                    val = False
                else:
                    try:
                        val = int(val_raw)
                    except ValueError:
                        try:
                            val = float(val_raw)
                        except ValueError:
                            val = val_raw

                set_clause = {col: val}

                where = None
                if where_part:
                    try:
                        where = parse_where(where_part)
                    except Exception as e:
                        print(f"Ошибка WHERE в UPDATE: {e}")
                        continue

                data = load_table_data(table_name)
                new_data = update(data, set_clause, where)
                save_table_data(table_name, new_data)
                updated_count = sum(1 for r in new_data if r.get(col) == val)
                print(f"Обновлено записей в таблице '{table_name}': {updated_count}")
                continue

            # --- CRUD: DELETE ---
            m = re.match(r"delete\s+from\s+(\w+)\s+where\s+(.*)", user_input, re.IGNORECASE)
            if m:
                table_name, where_part = m.groups()
                try:
                    where = parse_where(where_part)
                except Exception as e:
                    print(f"Ошибка WHERE в DELETE: {e}")
                    continue

                data = load_table_data(table_name)
                old_len = len(data)
                new_data = delete(data, where)
                save_table_data(table_name, new_data)
                deleted_count = old_len - len(new_data)
                print(f"Удалено записей из таблицы '{table_name}': {deleted_count}")
                continue

            print(f'Команда "{command}" не распознана. Введите help для справки.')

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Попробуйте снова.")


def main():
    run()
