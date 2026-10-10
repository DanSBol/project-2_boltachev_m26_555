from typing import Any, Dict, List

def get_schema_cols(metadata, table_name):
    """Возвращает список (name, type) без ID."""
    table = metadata.get(table_name)
    if not table:
        return None
    return [(c["name"], c["type"]) for c in table.get("columns", []) if c["name"].upper() != "ID"]

def insert(metadata, table_name, values):
    schema = get_schema_cols(metadata, table_name)
    if schema is None:
        raise ValueError(f"Таблица '{table_name}' не найдена")
    if len(values) != len(schema):
        raise ValueError("Количество значений не совпадает со схемой")

    # Валидация типов
    for (name, col_type), val in zip(schema, values):
        if col_type == "int":
            if not isinstance(val, int) or isinstance(val, bool):
                raise TypeError(f"{name}: ожидается int")
        elif col_type == "str":
            if not isinstance(val, str):
                raise TypeError(f"{name}: ожидается str")
        elif col_type == "bool":
            if not isinstance(val, bool):
                raise TypeError(f"{name}: ожидается bool")

    from .utils import load_table_data
    data = load_table_data(table_name)

    # Авто-ID
    ids = [r.get("ID", 0) for r in data]
    new_id = (max(ids) + 1) if ids else 1

    row = {"ID": new_id}
    for (name, _), val in zip(schema, values):
        row[name] = val
    data.append(row)
    return data

def select(data, where=None):
    if not where:
        return data
    key, val = next(iter(where.items()))
    return [r for r in data if r.get(key) == val]

def update(data, set_clause, where):
    key, val = next(iter(where.items()))
    updated = False
    for r in data:
        if r.get(key) == val:
            for k, v in set_clause.items():
                r[k] = v
            updated = True
    return data

def delete(data, where):
    key, val = next(iter(where.items()))
    return [r for r in data if r.get(key) != val]
