"""Декораторы: обработка ошибок, подтверждение действий, замер времени."""

import time

from prompt import prompt


def _copy_metadata(wrapper, func):
    """Копирует имя и docstring с оригинальной функции на обёртку."""
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def handle_db_errors(func):
    """Перехватывает исключения и печатает понятные сообщения об ошибках."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")

    return _copy_metadata(wrapper, func)


def confirm_action(action_name):
    """Запрашивает у пользователя подтверждение перед выполнением действия."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            question = f"Вы уверены, что хотите выполнить \"{action_name}\"? [y/n]: "
            response = prompt(question).strip().lower()
            if response != "y":
                print("Операция отменена пользователем.")
                return None
            return func(*args, **kwargs)

        return _copy_metadata(wrapper, func)

    return decorator


def log_time(func):
    """Печатает время выполнения функции в секундах."""

    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result

    return _copy_metadata(wrapper, func)
