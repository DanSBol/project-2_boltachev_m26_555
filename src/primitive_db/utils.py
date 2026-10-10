import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

METADATA_FILE = "db_meta.json"
DATA_DIR = "data"

def ensure_data_dir() -> None:
    Path(DATA_DIR).mkdir(exist_ok=True)

def load_metadata(filepath: str = METADATA_FILE) -> Dict[str, Any]:
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

def save_metadata(filepath: str, data: Dict[str, Any]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_table_data(table_name: str) -> List[Dict[str, Any]]:
    ensure_data_dir()
    filepath = Path(DATA_DIR) / f"{table_name}.json"

    if not filepath.exists():
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

def save_table_data(table_name: str, data: List[Dict[str, Any]]) -> None:
    ensure_data_dir()
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_cacher() -> Callable[[Any, Callable[[], Any]], Any]:
    cache: Dict[Any, Any] = {}

    def cache_result(key: Any, value_func: Callable[[], Any]) -> Any:
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result

_cached_get = create_cacher()

def make_select_key(
    table_name: str,
    where_clause: Optional[Dict[str, Any]] = None
) -> str:
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