"""Вспомогательные функции: файлы метаданных, данных таблиц и кэш."""

import json
import os

from .constants import DATA_DIR, METADATA_FILE


def ensure_data_dir():
    """Создаёт директорию данных, если её ещё нет."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_metadata(filepath=METADATA_FILE):
    """Загружает метаданные из JSON-файла; при ошибке возвращает пустой словарь."""
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        msg = (
            "Предупреждение: не удалось прочитать "
            f"{filepath}, используются пустые метаданные."
        )
        print(msg)
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _build_table_path(table_name):
    """Возвращает путь к JSON-файлу таблицы."""
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Загружает данные таблицы; при ошибке возвращает пустой список."""
    ensure_data_dir()
    filepath = _build_table_path(table_name)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                msg = (
                    f"Предупреждение: файл {filepath} содержит не список, "
                    "используется пустой набор данных."
                )
                print(msg)
                return []
            return data
    except (json.JSONDecodeError, IOError) as e:
        msg = (
            "Предупреждение: ошибка чтения "
            f"{filepath}: {e}. Используется пустой набор данных."
        )
        print(msg)
        return []


def save_table_data(table_name, data):
    """Сохраняет данные таблицы в JSON-файл."""
    ensure_data_dir()
    filepath = _build_table_path(table_name)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- Кэш выборок -------------------------------------------------------------

_cache = {}


def cached_get(key, value_func):
    """Возвращает значение из кэша, при отсутствии вычисляет и запоминает."""
    if key not in _cache:
        _cache[key] = value_func()
    return _cache[key]


def clear_cache():
    """Полностью очищает кэш. Вызывается после любой операции записи."""
    _cache.clear()


def make_select_key(table_name, where_clause=None):
    """Формирует ключ кэша для выборки с учётом условия where."""
    if not where_clause:
        return f"select:{table_name}:no_where"

    sorted_items = sorted(where_clause.items(), key=lambda x: x[0])
    where_str = ",".join(f"{k}={v}" for k, v in sorted_items)
    return f"select:{table_name}:{where_str}"


__all__ = [
    "METADATA_FILE",
    "DATA_DIR",
    "ensure_data_dir",
    "load_metadata",
    "save_metadata",
    "load_table_data",
    "save_table_data",
    "cached_get",
    "clear_cache",
    "make_select_key",
]
