import csv
import shutil
from datetime import datetime
from pathlib import Path

from bot.config import DB_FULL_PATH, config
from bot.database.models import get_all_tickets, get_all_users


async def export_users_to_csv() -> Path:
    users = await get_all_users()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = config.exports_dir / f"users_{timestamp}.csv"

    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["ID", "Telegram ID", "Ism", "Telefon", "Username", "Ro'yxatdan o'tgan sana"])
        for user in users:
            writer.writerow(
                [
                    user.get("id"),
                    user.get("telegram_id"),
                    user.get("full_name"),
                    user.get("phone"),
                    user.get("username"),
                    user.get("created_at"),
                ]
            )
    return file_path


async def export_tickets_to_csv() -> Path:
    tickets = await get_all_tickets(limit=100000)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = config.exports_dir / f"tickets_{timestamp}.csv"

    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "ID",
                "Telegram ID",
                "Ism",
                "Telefon",
                "Kategoriya",
                "Holat",
                "Admin ID",
                "Admin username",
                "Yaratilgan sana",
                "Qabul qilingan sana",
            ]
        )
        for ticket in tickets:
            writer.writerow(
                [
                    ticket.get("id"),
                    ticket.get("telegram_id"),
                    ticket.get("full_name"),
                    ticket.get("phone"),
                    ticket.get("category"),
                    ticket.get("status"),
                    ticket.get("admin_id"),
                    ticket.get("admin_username"),
                    ticket.get("created_at"),
                    ticket.get("accepted_at"),
                ]
            )
    return file_path


def backup_database() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config.backups_dir / f"backup_{timestamp}.db"
    shutil.copy2(DB_FULL_PATH, backup_path)
    return backup_path
