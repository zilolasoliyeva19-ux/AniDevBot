"""
Anime Bot - Asosiy ishga tushirish fayli.
aiogram 3.x + SQLite (aiosqlite).
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from anime_bot.config import config
from anime_bot.database.repo import setup_database
from anime_bot.middlewares.middlewares import UserMiddleware, ForceSubMiddleware
from anime_bot.handlers import user, admin


async def main():
    """Botni ishga tushirish."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger(__name__)

    if not config.bot_token:
        logger.error("BOT_TOKEN .env faylida sozlanmagan!")
        sys.exit(1)

    await setup_database()
    logger.info("SQLite baza tayyor")

    logger.info("Bot ishga tushmoqda...")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(ForceSubMiddleware())
    dp.callback_query.middleware(ForceSubMiddleware())

    dp.include_router(admin.router)
    dp.include_router(user.router)

    me = await bot.get_me()
    logger.info(f"Bot @{me.username} sifatida ishga tushdi!")

    # Har ishga tushganda rasmiy tavsifni tiklash.
    # BOT_TOKEN oshkor bo'lgan bo'lsa, uni BotFather orqali yangilash shart.
    try:
        await bot.set_my_description(
            "🎬 Anidev Anime — anime katalogi, yangiliklar va qismlarni topish uchun bot."
        )
        logger.info("Bot tavsifi standart matnga tiklandi.")
    except Exception as e:
        logger.warning(f"Bot tavsifini yangilab bo'lmadi: {e}")

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"Bot ishga tushdi!\n@{me.username} faol holatda.\n\n"
                f"Admin panel uchun /admin buyrug'ini yuboring."
            )
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga xabar yuborilmadi: {e}")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi foydalanuvchi tomonidan.")
