from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


# Database file lives at project root
DB_PATH = Path(__file__).resolve().parent.parent / "dashboard.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(schema_sql_path: Path) -> None:
    """
    Initialize database using schema.sql.
    Safe to run multiple times.
    """
    conn = connect()
    try:
        with open(schema_sql_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def upsert_device(
    device_id: str,
    location_tag: Optional[str],
    ip: Optional[str],
    first_seen_utc: str,
    last_seen_utc: str,
) -> None:
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO devices (
              device_id, location_tag, last_ip, first_seen_utc, last_seen_utc
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
              location_tag = COALESCE(excluded.location_tag, devices.location_tag),
              last_ip      = COALESCE(excluded.last_ip, devices.last_ip),
              last_seen_utc = excluded.last_seen_utc
            """,
            (device_id, location_tag, ip, first_seen_utc, last_seen_utc),
        )
        conn.commit()
    finally:
        conn.close()


def insert_checkin(row: Dict[str, Any]) -> int:
    """
    Insert a flattened check-in row.
    Returns the inserted row ID.
    """
    conn = connect()
    try:
        columns = ", ".join(row.keys())
        placeholders = ", ".join(["?"] * len(row))
        sql = f"INSERT INTO checkins ({columns}) VALUES ({placeholders})"
        cur = conn.execute(sql, list(row.values()))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_devices_latest() -> List[Dict[str, Any]]:
    """
    Return latest check-in per device for fleet view.
    """
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT c.*
            FROM checkins c
            JOIN (
              SELECT device_id, MAX(timestamp_utc) AS max_ts
              FROM checkins
              GROUP BY device_id
            ) latest
              ON c.device_id = latest.device_id
             AND c.timestamp_utc = latest.max_ts
            ORDER BY
              CASE c.computed_status
                WHEN 'red' THEN 3
                WHEN 'yellow' THEN 2
                ELSE 1
              END DESC,
              c.device_id ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_device_detail(device_id: str, limit: int = 20) -> Dict[str, Any]:
    """
    Return latest + recent history for a single device.
    """
    conn = connect()
    try:
        latest = conn.execute(
            """
            SELECT *
            FROM checkins
            WHERE device_id = ?
            ORDER BY timestamp_utc DESC
            LIMIT 1
            """,
            (device_id,),
        ).fetchone()

        history = conn.execute(
            """
            SELECT *
            FROM checkins
            WHERE device_id = ?
            ORDER BY timestamp_utc DESC
            LIMIT ?
            """,
            (device_id, limit),
        ).fetchall()

        return {
            "latest": dict(latest) if latest else None,
            "history": [dict(r) for r in history],
        }
    finally:
        conn.close()

