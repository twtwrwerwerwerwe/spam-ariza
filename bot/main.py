import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database.db import init_db
from bot.handlers import admin, common, user
from bot.middlewares.db_middleware import DatabaseMiddleware, LoggingMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.7))
    dp.message.middleware(DatabaseMiddleware())

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot ishga tushdi.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot to'xtatildi.")
