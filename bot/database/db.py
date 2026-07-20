import logging

import aiosqlite

from bot.config import DB_FULL_PATH

logger = logging.getLogger(__name__)

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    username TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

CREATE_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,
    full_name TEXT,
    phone TEXT,
    category TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    admin_id INTEGER,
    admin_username TEXT,
    group_message_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    accepted_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

CREATE_ADMINS_TABLE = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    added_by INTEGER,
    added_at TEXT DEFAULT (datetime('now'))
);
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status);",
    "CREATE INDEX IF NOT EXISTS idx_tickets_telegram_id ON tickets (telegram_id);",
    "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);",
]


async def init_db() -> None:
    """Create all tables and indexes if they do not exist yet."""
    async with aiosqlite.connect(DB_FULL_PATH) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_TICKETS_TABLE)
        await db.execute(CREATE_ADMINS_TABLE)
        await db.execute(CREATE_SETTINGS_TABLE)
        for index_sql in CREATE_INDEXES:
            await db.execute(index_sql)
        await db.commit()
    logger.info("Ma'lumotlar bazasi tayyor: %s", DB_FULL_PATH)


def get_connection() -> aiosqlite.Connection:
    """Return a new aiosqlite connection context manager."""
    return aiosqlite.connect(DB_FULL_PATH)
