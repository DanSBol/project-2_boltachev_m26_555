import json
import os

METADATA_FILE = "db_meta.json"
DATA_DIR = "data"

def ensure_data_dir():
    # Аналог Path(DATA_DIR).mkdir(exist_ok=True)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_metadata(filepath=METADATA_FILE):
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
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _build_table_path(table_name):
    return os.path.join(DATA_DIR, f"{table_name}.json")

def load_table_data(table_name):
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
    ensure_data_dir()
    filepath = _build_table_path(table_name)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result

_cached_get = create_cacher()

def make_select_key(table_name, where_clause=None):
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
    "_cached_get",
    "make_select_key",
]