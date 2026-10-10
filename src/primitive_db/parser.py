import ast
from typing import Any, Dict, List, Union


def parse_values(values_str: str) -> Union[List[Any], Any]:
    if not values_str or not values_str.strip():
        raise ValueError("Пустая строка значений")

    try:
        result = ast.literal_eval(values_str.strip())

        if isinstance(result, (list, tuple, dict)):
            return result
        return [result]
    except (ValueError, SyntaxError) as e:
        msg = (
            f"Неверный формат значений: '{values_str}'. "
            "Ожидаются литералы Python, например: ('Alice', 30) или {'age': 29}"
        )
        raise ValueError(msg) from e

def normalize_value(raw_value: Any) -> Any:
    if isinstance(raw_value, str):
        lower = raw_value.lower()
        if lower in ("true", "false"):
            return lower == "true"
        return raw_value.strip()
    return raw_value

def parse_insert_row(values_input: str) -> List[Any]:
    raw_data = parse_values(values_input)

    if isinstance(raw_data, dict):
        return list(raw_data.values())

    if isinstance(raw_data, (list, tuple)):
        return [normalize_value(v) for v in raw_data]

    return [normalize_value(raw_data)]

def parse_where_clause(where_input: str) -> Dict[str, Any]:
    if not where_input:
        return {}

    where_input = where_input.strip()

    if "=" in where_input:
        key, _, val = where_input.partition("=")
        key = key.strip()
        val = val.strip()

        try:
            if "." in val:
                val = float(val)
            else:
                val = int(val)
        except ValueError:
            val = val.strip('"\'')

        return {key: val}

    msg = (
        f"Неподдерживаемый формат WHERE: '{where_input}'. "
        "Используйте формат key=value"
    )
    raise ValueError(msg)