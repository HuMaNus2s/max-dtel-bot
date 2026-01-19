import sqlite3
import os
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dtel_database.db")

@contextmanager
def get_connection():
    """Контекстный менеджер для соединения с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def check_db_status():
    """Проверяет состояние базы данных"""

    if not os.path.exists(DB_PATH):
        logger.warning(f"Database file NOT FOUND! Expected path: {os.path.abspath(DB_PATH)}")
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

            logging.info(f"Database initialized!")
            return True

    except sqlite3.Error as e:
        logging.exception(f"Error SQLite: {e}")
        return False
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return False


class Database:

    @staticmethod
    def get_chat_ids_for_group(group_name: str) -> list[int]:
        """
        Возвращает все max_chat_id для данной мнемонической группы
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
                (group_name,)
            )
            return [row["max_id"] for row in cursor.fetchall()]

    @staticmethod
    def is_key_allowed_for_group(api_key: str, group_name: str) -> bool:
        """
        Проверяет, имеет ли ключ доступ к указанной группе
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
                (api_key, group_name)
            )
            return cursor.fetchone() is not None