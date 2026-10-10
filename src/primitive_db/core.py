SUPPORTED_TYPES = {"int", "str", "bool"}

def parse_columns(col_args: list[str]) -> list[tuple[str, str]]:
    columns = []
    for arg in col_args:
        if ":" not in arg:
            raise ValueError(f"Некорректный формат столбца: {arg}")
        name, typ = arg.split(":", 1)
        name = name.strip()
        typ = typ.strip().lower()
        if not name:
            raise ValueError(f"Имя столбца пустое в: {arg}")
        if typ not in SUPPORTED_TYPES:
            raise ValueError(f"Неподдерживаемый тип данных: {typ} в {arg}")
        columns.append((name, typ))
    return columns

def create_table(metadata: dict, table_name: str, col_args: list[str]) -> dict:
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')

    user_columns = parse_columns(col_args)

    final_columns = [("ID", "int")] + user_columns

    metadata[table_name] = {
        "columns": final_columns,
    }
    return metadata

def drop_table(metadata: dict, table_name: str) -> dict:
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    del metadata[table_name]
    return metadata

def list_tables(metadata: dict) -> list[str]:
    return list(metadata.keys())