"""Публичный API пакета primitive_db."""

from .core import delete, drop_table, get_table_stats, insert, select, update
from .utils import ensure_data_dir, load_metadata, save_metadata

__all__ = [
    "insert",
    "select",
    "delete",
    "drop_table",
    "update",
    "get_table_stats",
    "ensure_data_dir",
    "load_metadata",
    "save_metadata",
]
