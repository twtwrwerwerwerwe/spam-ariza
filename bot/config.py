import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Majburiy muhit o'zgaruvchisi topilmadi: {name}. "
            f".env faylini tekshiring."
        )
    return value


@dataclass(frozen=True)
class Config:
    bot_token: str = field(default_factory=lambda: _require_env("BOT_TOKEN"))
    admin_group_id: int = field(
        default_factory=lambda: int(os.getenv("ADMIN_GROUP_ID", "-1003399313219"))
    )
    super_admin_id: int = field(
        default_factory=lambda: int(os.getenv("SUPER_ADMIN_ID", "6302873072"))
    )
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "database.db"))
    logs_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
    exports_dir: Path = field(default_factory=lambda: BASE_DIR / "exports")
    backups_dir: Path = field(default_factory=lambda: BASE_DIR / "backups")


config = Config()

config.logs_dir.mkdir(parents=True, exist_ok=True)
config.exports_dir.mkdir(parents=True, exist_ok=True)
config.backups_dir.mkdir(parents=True, exist_ok=True)

DB_FULL_PATH = str(BASE_DIR / config.db_path)

TICKET_CATEGORIES = [
    "🛠  Umrbodlik spam",
    "🔐  Yillik spam",
    "🔐  Haftalik spam",
    "🥶  Muzlagan akkauntlar 💯",
    "🛡   Ban bo'lgan akauntlar",
    "⭐️  Telegram Premium",
    "⚡️  Gurhlarga odam qo'shish",
]

TICKET_STATUS_NEW = "new"
TICKET_STATUS_ACCEPTED = "accepted"
TICKET_STATUS_CLOSED = "closed"
