"""Основная бизнес-логика: CRUD-операции над таблицами и статистика."""

import os

from .constants import DATA_DIR, ID_COLUMN
from .decorators import confirm_action, handle_db_errors, log_time
from .utils import (
    _cached_get,
    clear_cache,
    load_table_data,
    make_select_key,
    save_table_data,
)


@handle_db_errors
@log_time
def select(table_name, where=None):
    """Выбирает строки таблицы с фильтрацией по всем условиям where."""
    data = load_table_data(table_name)
    key = make_select_key(table_name, where or {})

    def fetch():
        if not where:
            return data
        return [
            row for row in data
            if all(row.get(col) == val for col, val in where.items())
        ]

    return _cached_get(key, fetch)


@handle_db_errors
@log_time
def insert(table_name, rows):
    """Вставляет строки в таблицу, автоматически назначая следующие id."""
    if not rows:
        return 0

    data = load_table_data(table_name)
    ids = [r.get(ID_COLUMN) for r in data if isinstance(r.get(ID_COLUMN), int)]
    next_id = (max(ids) + 1) if ids else 1

    for row in rows:
        if ID_COLUMN not in row or row[ID_COLUMN] is None:
            row[ID_COLUMN] = next_id
            next_id += 1

    data.extend(rows)
    save_table_data(table_name, data)
    clear_cache()
    return len(rows)


@handle_db_errors
@log_time
@confirm_action("удаление строк из таблицы")
def delete(table_name, where=None):
    """Удаляет строки по условию; без условия удаляет все строки таблицы."""
    data = load_table_data(table_name)
    original_len = len(data)

    if not where:
        data.clear()
    else:
        data = [
            row for row in data
            if not all(row.get(col) == val for col, val in where.items())
        ]

    save_table_data(table_name, data)
    clear_cache()
    return original_len - len(data)


@handle_db_errors
@log_time
@confirm_action("удаление таблицы и всех её данных")
def drop_table(table_name):
    """Полностью удаляет таблицу (файл с данными)."""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        clear_cache()
        return True
    return False


@handle_db_errors
@log_time
def update(table_name, set_clause, where):
    """Обновляет поля set_clause у строк, подходящих под все условия where."""
    if not where:
        raise ValueError("Для update требуется непустое условие where")

    data = load_table_data(table_name)
    updated_count = 0

    for row in data:
        if all(row.get(col) == val for col, val in where.items()):
            for set_key, set_value in set_clause.items():
                row[set_key] = set_value
            updated_count += 1

    save_table_data(table_name, data)
    clear_cache()
    return updated_count


@handle_db_errors
@log_time
def get_table_stats(table_name):
    """Возвращает статистику по таблице: число строк, колонки, пример строки."""
    data = load_table_data(table_name)
    if not data:
        return {
            "table": table_name,
            "row_count": 0,
            "columns": [],
            "sample_row": None,
        }

    columns = list(data[0].keys())
    return {
        "table": table_name,
        "row_count": len(data),
        "columns": columns,
        "sample_row": data[0],
    }
