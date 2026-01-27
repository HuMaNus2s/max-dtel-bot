import sqlite3
import os
from contextlib import contextmanager
import logging
from os import getenv
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

raw_path = getenv("DATABASE_PATH")
if not raw_path:
    raise ValueError("DATABASE_PATH is not specified in .env")

parsed = urlparse(raw_path)

if parsed.scheme in ("http", "https"):
    DATABASE_PATH = raw_path
elif parsed.scheme == "sqlite":
    DATABASE_PATH = parsed.path.lstrip("/")
else:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(raw_path):
        DATABASE_PATH = os.path.join(project_root, raw_path)
    else:
        DATABASE_PATH = raw_path


@contextmanager
def get_connection():
    """
    Открывает подключение к базе данных и потом закрывает его.

    Эта функция используется через "with", чтобы не забывать закрывать соединение.
    
    Пример:
        with get_connection() as conn:
            pass
    """
    if DATABASE_PATH.startswith("http"):
        raise ValueError("HTTP/HTTPS база не поддерживается SQLite")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # чтобы можно было обращаться к колонкам по имени
    try:
        yield conn
    finally:
        conn.close()


def check_db_status():
    """
    Проверяет, всё ли нормально с базой данных.

    1. Смотрит, существует ли файл базы.
    2. Проверяет, есть ли нужные таблицы.
    3. Если всё ок - возвращает True, иначе False.
    """
    if DATABASE_PATH.startswith("http"):
        return True

    if not os.path.exists(DATABASE_PATH):
        logger.warning(f"Database file NOT FOUND! Expected path: {os.path.abspath(DATABASE_PATH)}")
        return False

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            tables = ["groups", "max_groups", "keys", "group_api_keys"]
            missing_tables = []

            for table in tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    missing_tables.append(table)

            if missing_tables:
                return False

            return True

    except sqlite3.Error as e:
        logger.exception(f"SQLite ошибка: {e}")
        return False
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
        return False


class Database:
    """
    Класс для работы с базой данных.

    Здесь собраны функции, которые делают SQL-запросы.
    """

    @staticmethod
    def get_chat_ids_for_group(group_name: str) -> list[int]:
        """
        Получает все chat_id (max_id) для конкретной группы.

        group_name — это название группы из таблицы groups.
        Возвращает список чисел.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT mg.max_id
                FROM max_groups mg
                JOIN groups g ON mg.group_id = g.id
                WHERE g.group_name = ?
                """,
                (group_name,),
            )
            return [row["max_id"] for row in cursor.fetchall()]

    @staticmethod
    def is_key_allowed_for_group(api_key: str, group_name: str) -> bool:
        """
        Проверяет, можно ли использовать ключ для указанной группы.

        Если ключ есть в таблице и связан с группой — вернёт True.
        Иначе False.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM group_api_keys gak
                JOIN keys k ON gak.key_id = k.id
                JOIN groups g ON gak.group_id = g.id
                WHERE k.api_key = ? AND g.group_name = ?
                """,
                (api_key, group_name),
            )
            return cursor.fetchone() is not None
