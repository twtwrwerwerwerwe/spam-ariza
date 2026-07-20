from datetime import datetime, timezone
from typing import Any, Optional

from bot.config import (
    TICKET_STATUS_ACCEPTED,
    TICKET_STATUS_NEW,
    config,
)
from bot.database.db import get_connection


def _row_to_dict(row) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


async def _fetch_all_as_dicts(cursor) -> list[dict[str, Any]]:
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def upsert_user(
    telegram_id: int,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    username: Optional[str] = None,
) -> None:
    async with get_connection() as db:
        db.row_factory = None
        existing = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await existing.fetchone()
        if row is None:
            await db.execute(
                """
                INSERT INTO users (telegram_id, full_name, phone, username)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, full_name, phone, username),
            )
        else:
            fields = []
            values: list[Any] = []
            if full_name is not None:
                fields.append("full_name = ?")
                values.append(full_name)
            if phone is not None:
                fields.append("phone = ?")
                values.append(phone)
            if username is not None:
                fields.append("username = ?")
                values.append(username)
            if fields:
                values.append(telegram_id)
                await db.execute(
                    f"UPDATE users SET {', '.join(fields)} WHERE telegram_id = ?",
                    values,
                )
        await db.commit()


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict[str, Any]]:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def get_all_users() -> list[dict[str, Any]]:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute("SELECT * FROM users ORDER BY id DESC")
        return await _fetch_all_as_dicts(cursor)


async def count_users() -> int:
    async with get_connection() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

async def create_ticket(
    user_id: int,
    telegram_id: int,
    full_name: str,
    phone: str,
    category: str,
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO tickets (user_id, telegram_id, full_name, phone, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, telegram_id, full_name, phone, category, TICKET_STATUS_NEW),
        )
        await db.commit()
        return cursor.lastrowid


async def set_ticket_group_message_id(ticket_id: int, message_id: int) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE tickets SET group_message_id = ? WHERE id = ?",
            (message_id, ticket_id),
        )
        await db.commit()


async def get_ticket(ticket_id: int) -> Optional[dict[str, Any]]:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()
        return _row_to_dict(row)


async def accept_ticket(ticket_id: int, admin_id: int, admin_username: str) -> bool:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute(
            "SELECT status FROM tickets WHERE id = ?", (ticket_id,)
        )
        row = await cursor.fetchone()
        if row is None or row["status"] != TICKET_STATUS_NEW:
            return False
        accepted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            UPDATE tickets
            SET status = ?, admin_id = ?, admin_username = ?, accepted_at = ?
            WHERE id = ?
            """,
            (TICKET_STATUS_ACCEPTED, admin_id, admin_username, accepted_at, ticket_id),
        )
        await db.commit()
        return True


async def get_all_tickets(limit: int = 50) -> list[dict[str, Any]]:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute(
            "SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,)
        )
        return await _fetch_all_as_dicts(cursor)


async def get_tickets_by_status(status: str, limit: int = 50) -> list[dict[str, Any]]:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC LIMIT ?",
            (status, limit),
        )
        return await _fetch_all_as_dicts(cursor)


async def count_tickets() -> int:
    async with get_connection() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM tickets")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def count_tickets_by_status(status: str) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tickets WHERE status = ?", (status,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def count_tickets_today() -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tickets WHERE date(created_at) = date('now')"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------------------------------------------------------------------------
# Admins
# ---------------------------------------------------------------------------

async def add_admin(telegram_id: int, added_by: int) -> bool:
    async with get_connection() as db:
        try:
            await db.execute(
                "INSERT INTO admins (telegram_id, added_by) VALUES (?, ?)",
                (telegram_id, added_by),
            )
            await db.commit()
            return True
        except Exception:
            return False


async def remove_admin(telegram_id: int) -> bool:
    async with get_connection() as db:
        cursor = await db.execute(
            "DELETE FROM admins WHERE telegram_id = ?", (telegram_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def is_admin(telegram_id: int) -> bool:
    if telegram_id == config.super_admin_id:
        return True
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return row is not None


async def get_all_admins() -> list[dict[str, Any]]:
    async with get_connection() as db:
        db.row_factory = _row_factory
        cursor = await db.execute("SELECT * FROM admins ORDER BY id DESC")
        return await _fetch_all_as_dicts(cursor)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

async def get_setting(key: str) -> Optional[str]:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_setting(key: str, value: str) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await db.commit()


def _row_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))
