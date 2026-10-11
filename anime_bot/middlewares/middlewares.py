"""
Middlewares - Majburiy obuna tekshiruvi va foydalanuvchi ro'yxatdan o'tkazish.
"""
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Any, Awaitable, Callable

from anime_bot.config import config
from anime_bot.database import repo
from anime_bot.keyboards.keyboards import force_sub_kb

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """Har bir xabarda foydalanuvchini bazaga qo'shadi/yangilaydi va ban tekshiradi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            # Foydalanuvchini bazaga qo'shish yoki yangilash
            await repo.get_or_create_user(
                tg_user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
            )

            # Ban tekshiruvi
            is_banned = await repo.is_user_banned(user.id)
            if is_banned:
                if isinstance(event, (Message, CallbackQuery)):
                    await event.answer(
                        "🚫 Siz botdan foydalanish taqiqlangansiz.",
                        show_alert=True if isinstance(event, CallbackQuery) else None,
                    )
                return  # Handler ni chaqirmaymiz

        return await handler(event, data)


class ForceSubMiddleware(BaseMiddleware):
    """Majburiy obuna tekshiruvi - kanallarga obuna bo'lishni talab qiladi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Adminlar uchun tekshiruvni o'tkazib yuboramiz
        if user.id in config.admin_ids or await repo.is_db_admin(user.id):
            data["is_admin"] = True
            return await handler(event, data)

        data["is_admin"] = False

        # Majburiy obuna kanallarini olish
        force_subs = await repo.get_force_subs()
        if not force_subs:
            # Kanallar sozlanmagan bo'lsa, o'tkazib yuboramiz
            return await handler(event, data)

        # Bot instance olish
        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        # Har bir kanalga obuna tekshiruvi.
        not_subscribed = []
        for sub in force_subs:
            channel_username = (sub.get("channel_username") or "").strip()
            if not channel_username:
                not_subscribed.append(sub)
                continue

            chat_id = channel_username if channel_username.startswith("@") else f"@{channel_username}"
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user.id)
                status = str(member.status)
                is_member = status in ("creator", "administrator", "member")
                if status == "restricted":
                    is_member = bool(getattr(member, "is_member", False))
                if not is_member:
                    not_subscribed.append(sub)
            except Exception as e:
                logger.warning(
                    "Obuna tekshiruvda xato: kanal=%s user_id=%s xato=%s",
                    channel_username, user.id, e,
                )
                not_subscribed.append(sub)

        if not_subscribed:
            # Obuna bo'lmagan kanallar mavjud
            if isinstance(event, Message):
                await event.answer(
                    "🔔 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling!",
                    reply_markup=force_sub_kb(not_subscribed),
                )
                return
            elif isinstance(event, CallbackQuery):
                # /start dagi check_sub callback dan tashqari barchasini bloklash
                if event.data == "check_sub":
                    return await handler(event, data)
                await event.answer(
                    "⚠️ Iltimos, avval kanallarga obuna bo'ling!",
                    show_alert=True,
                )
                return

        return await handler(event, data)
