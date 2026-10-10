from .decorators import confirm_action, handle_db_errors, log_time
from .utils import _cached_get, load_table_data, make_select_key, save_table_data


@handle_db_errors
@log_time
def select(table_name, where=None):
    data = load_table_data(table_name)
    key = make_select_key(table_name, where or {})

    def fetch():
        if not where:
            return data
        key_col, val = next(iter(where.items()))
        return [row for row in data if row.get(key_col) == val]

    return _cached_get(key, fetch)

@handle_db_errors
@log_time
def insert(table_name, rows):
    if not rows:
        return 0

    data = load_table_data(table_name)
    ids = [r.get("id") for r in data if isinstance(r.get("id"), int)]
    next_id = (max(ids) + 1) if ids else 1

    for row in rows:
        if "id" not in row or row["id"] is None:
            row["id"] = next_id
            next_id += 1

    data.extend(rows)
    save_table_data(table_name, data)
    return len(rows)

@handle_db_errors
@log_time
@confirm_action("удаление строк из таблицы")
def delete(table_name, where=None):
    data = load_table_data(table_name)
    original_len = len(data)

    if not where:
        data.clear()
    else:
        key_col, val = next(iter(where.items()))
        data = [row for row in data if row.get(key_col) != val]

    save_table_data(table_name, data)
    return original_len - len(data)

@handle_db_errors
@log_time
@confirm_action("удаление таблицы и всех её данных")
def drop_table(table_name):
    from pathlib import Path

    from .utils import DATA_DIR

    filepath = Path(DATA_DIR) / f"{table_name}.json"
    if filepath.exists():
        filepath.unlink()
        return True
    return False

@handle_db_errors
@log_time
def update(table_name, set_clause, where):
    data = load_table_data(table_name)
    updated_count = 0
    key_col, val = next(iter(where.items()))

    for r in data:
        if r.get(key_col) == val:
            for k, v in set_clause.items():
                r[k] = v
            updated_count += 1

    save_table_data(table_name, data)
    return updated_count

@handle_db_errors
@log_time
def get_table_stats(table_name):
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