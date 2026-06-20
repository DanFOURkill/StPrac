"""Простая работа с SQLite для учебного проекта InfoCollector."""

import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "database.db"


def get_connection() -> sqlite3.Connection:
    """Создаёт подключение к базе данных SQLite."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Создаёт таблицу истории, если её ещё нет."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT NOT NULL,
                query TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                fragments TEXT NOT NULL,
                links_count INTEGER NOT NULL
            )
            """
        )


def save_result(result: dict[str, Any]) -> int:
    """Сохраняет результат сбора информации и возвращает ID записи."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO results (collected_at, query, url, title, fragments, links_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result["collected_at"],
                result["query"],
                result["url"],
                result["title"],
                json.dumps(result["fragments"], ensure_ascii=False),
                result["links_count"],
            ),
        )
        return int(cursor.lastrowid)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Преобразует строку SQLite в словарь для ответа API."""

    data = dict(row)
    data["fragments"] = json.loads(data["fragments"])
    return data


def get_result(result_id: int) -> dict[str, Any] | None:
    """Возвращает одну запись истории по ID."""

    with get_connection() as connection:
        row = connection.execute("SELECT * FROM results WHERE id = ?", (result_id,)).fetchone()
        return row_to_dict(row) if row else None


def get_history() -> list[dict[str, Any]]:
    """Возвращает все записи истории от новых к старым."""

    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
        return [row_to_dict(row) for row in rows]


def delete_result(result_id: int) -> bool:
    """Удаляет запись истории. Возвращает True, если запись была удалена."""

    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM results WHERE id = ?", (result_id,))
        return cursor.rowcount > 0
