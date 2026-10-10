import json
from pathlib import Path

METADATA_FILE = "db_meta.json"

def load_metadata(filepath: str = METADATA_FILE) -> dict:
    path = Path(filepath)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError: # нет файла
        return {}
    except json.JSONDecodeError: # битый файл
        return {}

def save_metadata(filepath: str, data: dict) -> None:
    path = Path(filepath)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)