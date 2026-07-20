from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.database.models import is_admin


class IsAdminFilter(BaseFilter):
    """Passes only if the message author is the super admin or a registered admin."""

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return await is_admin(message.from_user.id)


class IsSuperAdminFilter(BaseFilter):
    """Passes only if the message author is the hard-coded super admin."""

    def __init__(self, super_admin_id: int) -> None:
        self.super_admin_id = super_admin_id

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return message.from_user.id == self.super_admin_id
