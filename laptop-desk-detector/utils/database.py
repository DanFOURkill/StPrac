"""Модуль для работы с SQLite-историей запросов."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "history.db"


def get_connection() -> sqlite3.Connection:
    """Создаёт подключение к базе данных и включает доступ к колонкам по имени."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Создаёт таблицу истории, если она ещё не существует."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                laptops_count INTEGER,
                avg_laptops_count REAL,
                max_laptops_count INTEGER,
                confidence_threshold REAL NOT NULL,
                result_path TEXT NOT NULL,
                processing_time_seconds REAL NOT NULL
            )
            """
        )
        conn.commit()


def add_request(record: Dict[str, Any]) -> int:
    """Добавляет запись об обработке файла и возвращает id записи."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO requests (
                timestamp, filename, file_type, laptops_count, avg_laptops_count,
                max_laptops_count, confidence_threshold, result_path, processing_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["timestamp"],
                record["filename"],
                record["file_type"],
                record.get("laptops_count"),
                record.get("avg_laptops_count"),
                record.get("max_laptops_count"),
                record["confidence_threshold"],
                record["result_path"],
                record["processing_time_seconds"],
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Возвращает историю запросов: последние записи идут первыми."""
    query = "SELECT * FROM requests ORDER BY id DESC"
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]
