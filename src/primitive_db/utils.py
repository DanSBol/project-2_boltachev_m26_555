import json
import os
from pathlib import Path

METADATA_FILE = "db_meta.json"
DATA_DIR = "data"

def ensure_data_dir():
    Path(DATA_DIR).mkdir(exist_ok=True)

def load_metadata(filepath=METADATA_FILE):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_metadata(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_table_data(table_name):
    ensure_data_dir()
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Если файл битый — возвращаем пустой список, чтобы не ломать CLI
        return []

def save_table_data(table_name, data):
    ensure_data_dir()
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)