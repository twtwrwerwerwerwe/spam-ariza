import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message


class ThrottlingMiddleware(BaseMiddleware):
    """Blocks a user from sending more than one update per `rate_limit` seconds."""

    def __init__(self, rate_limit: float = 0.7) -> None:
        self.rate_limit = rate_limit
        self._last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            last = self._last_call.get(user.id)
            if last is not None and (now - last) < self.rate_limit:
                if isinstance(event, Message):
                    return None
            self._last_call[user.id] = now
        return await handler(event, data)
