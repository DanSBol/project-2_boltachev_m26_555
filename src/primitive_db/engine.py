import prompt
import shlex
from .core import create_table, drop_table, list_tables
from .utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"

def print_help():
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> ... - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

def run():
    """Основной цикл CLI для управления таблицами."""
    while True:
        try:
            user_input = prompt.string(">>> Введите команду: ").strip()
            if not user_input:
                continue

            args = shlex.split(user_input)
            command = args[0].lower()

            if command == "help":
                print_help()
                continue

            if command == "exit":
                print("Выход из программы.")
                break

            metadata = load_metadata(METADATA_FILE)

            if command == "create_table":
                if len(args) < 3:
                    print("Некорректное значение: недостаточно аргументов для create_table.")
                    print('Пример: create_table users name:str age:int is_active:bool')
                    continue
                table_name = args[1]
                col_args = args[2:]
                try:
                    create_table(metadata, table_name, col_args)
                    save_metadata(METADATA_FILE, metadata)
                    cols_str = ", ".join(f"{n}:{t}" for n, t in metadata[table_name]["columns"])
                    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_str}')
                except ValueError as e:
                    print(str(e))
                continue

            if command == "drop_table":
                if len(args) != 2:
                    print("Некорректное значение: требуется имя таблицы.")
                    print('Пример: drop_table users')
                    continue
                table_name = args[1]
                try:
                    drop_table(metadata, table_name)
                    save_metadata(METADATA_FILE, metadata)
                    print(f'Таблица "{table_name}" успешно удалена.')
                except ValueError as e:
                    print(str(e))
                continue

            if command == "list_tables":
                metadata = load_metadata(METADATA_FILE)  # перезагрузить на всякий случай
                tables = list_tables(metadata)
                if not tables:
                    print("Таблиц пока нет.")
                else:
                    for t in tables:
                        print(f"- {t}")
                continue

            print(f'Функции "{command}" нет. Попробуйте снова.')
            print_help()

        except Exception as e: # Все остальные ошибки
            print(f"Произошла ошибка: {e}")
            print("Попробуйте снова.")