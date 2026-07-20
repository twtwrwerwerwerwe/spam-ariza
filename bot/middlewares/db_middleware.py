import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.database.models import upsert_user

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Registers/updates the user in the database on every private message."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.chat.type == "private" and event.from_user:
            user = event.from_user
            try:
                await upsert_user(
                    telegram_id=user.id,
                    username=user.username,
                )
            except Exception:
                logger.exception("Foydalanuvchini bazaga yozishda xatolik: %s", user.id)
        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    """Logs every incoming update for observability."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            logger.info(
                "Update: chat_id=%s user_id=%s text=%r",
                event.chat.id,
                event.from_user.id if event.from_user else None,
                event.text,
            )
        return await handler(event, data)
