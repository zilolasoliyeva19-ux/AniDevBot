"""
Foydalanuvchi handlerlari - start, qidiruv, anime ko'rish, epizodlar, sevimlilar.
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.fsm.context import FSMContext

from anime_bot.config import config
from anime_bot.database import repo
from anime_bot.keyboards import keyboards as kb
from anime_bot.states.states import SearchStates

logger = logging.getLogger(__name__)
router = Router(name="user")

@router.message(F.text == "❌ Bekor qilish")
async def cancel_search_early(message: Message, state: FSMContext):
    """Bekor qilishni qidiruv FSM handlerlaridan oldin bajarish."""
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=kb.main_menu_kb())



# ==================== /START ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, is_admin: bool = False):
    """Botni ishga tushirish - bosh menyu."""
    await state.clear()

    welcome_text = (
        f"👋 Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"🎬 <b>Anime Bot</b>ga xush kelibsiz!\n"
        f"Bu yerda o'zingiz yoqtirgan animelarni topishingiz,\n"
        f"qismlarini yuklab olishingiz va sevimlilar saqlashingiz mumkin.\n\n"
        f"📥 Kerakli bo'limni tanlang 👇"
    )

    if is_admin:
        await message.answer(welcome_text, reply_markup=kb.admin_menu_kb())
    else:
        await message.answer(welcome_text, reply_markup=kb.main_menu_kb())


# ==================== ASOSIY MENYU TUGMALARI ====================

@router.message(F.text == "🔍 Qidirish")
async def menu_search(message: Message, state: FSMContext):
    """Qidiruv menyusi."""
    await state.clear()
    await message.answer(
        "🔍 <b>Qidiruv turini tanlang:</b>",
        reply_markup=kb.search_menu_kb(),
    )


@router.message(F.text == "🎭 Janrlar")
async def menu_genres(message: Message):
    """Janrlar ro'yxati."""
    genres = await repo.get_all_genres()
    if not genres:
        await message.answer("Hozircha janrlar mavjud emas.")
        return
    await message.answer(
        "🎭 <b>Janrlar ro'yxati:</b>\nKerakli janrni tanlang:",
        reply_markup=kb.genres_kb(genres),
    )


@router.message(F.text == "⭐ Sevimlilar")
async def menu_favorites(message: Message):
    """Sevimli animelar ro'yxati."""
    favorites = await repo.get_user_favorites(message.from_user.id)
    if not favorites:
        await message.answer(
            "⭐ Sizda hali sevimli animelar yo'q.\n"
            "Anime sahifasida ⭐ tugmasi orqali qo'shishingiz mumkin.",
            reply_markup=kb.main_menu_kb(),
        )
        return
    await message.answer(
        f"⭐ <b>Sevimli animelaringiz ({len(favorites)} ta):</b>",
        reply_markup=kb.anime_list_kb(favorites),
    )


@router.message(F.text == "🔥 Top Anime")
async def menu_top(message: Message):
    """Eng ko'p ko'rilgan animelar."""
    top = await repo.get_top_animes(10)
    if not top:
        await message.answer("Hozircha animelar mavjud emas.")
        return
    await message.answer(
        "🔥 <b>Eng ko'p ko'rilgan animelar:</b>",
        reply_markup=kb.anime_list_kb(top),
    )


@router.message(F.text == "📊 Statistika")
async def menu_stats(message: Message):
    """Bot statistikasi (foydalanuvchi uchun ochiq)."""
    stats = await repo.get_stats()
    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🎬 Jami animelar: <b>{stats['total_animes']}</b>\n"
        f"📺 Jami epizodlar: <b>{stats['total_episodes']}</b>\n"
    )
    if stats.get("top_animes"):
        text += "\n🔥 <b>Top 5 eng ko'p ko'rilgan:</b>\n"
        for i, anime in enumerate(stats["top_animes"], 1):
            views = anime.get("views", 0)
            text += f"{i}. {anime['title']} — 👁 {views}\n"

    await message.answer(text)


@router.message(F.text == "🔙 Bosh menyu")
async def menu_back_to_main(message: Message, state: FSMContext):
    """Bosh menyuga qaytish."""
    await state.clear()
    is_admin = message.from_user.id in config.admin_ids or await repo.is_db_admin(message.from_user.id)
    if is_admin:
        await message.answer("📋 Bosh menyu:", reply_markup=kb.admin_menu_kb())
    else:
        await message.answer("📋 Bosh menyu:", reply_markup=kb.main_menu_kb())


# ==================== QIDIRUV TURLARI ====================

@router.message(F.text == "📖 Nomi bo'yicha")
async def search_by_title_start(message: Message, state: FSMContext):
    """Nomi bo'yicha qidiruvni boshlash."""
    await state.set_state(SearchStates.waiting_title)
    await message.answer(
        "📖 Anime nomini (yoki uning bir qismini) kiriting:",
        reply_markup=kb.cancel_kb(),
    )


@router.message(SearchStates.waiting_title)
async def search_by_title_process(message: Message, state: FSMContext):
    """Nomi bo'yicha qidiruv natijalari."""
    query = message.text.strip()
    if not query:
        await message.answer("Iltimos, to'g'ri nom kiriting.")
        return

    results = await repo.search_animes_by_title(query)
    await state.clear()

    if not results:
        await message.answer(
            f"❌ \"{query}\" bo'yicha hech narsa topilmadi.",
            reply_markup=kb.main_menu_kb(),
        )
        return

    await message.answer(
        f"✅ <b>{len(results)} ta anime topildi:</b>",
        reply_markup=kb.anime_list_kb(results),
    )
    await message.answer("📋 Bosh menyu:", reply_markup=kb.main_menu_kb())


@router.message(F.text == "📅 Yil bo'yicha")
async def search_by_year_start(message: Message, state: FSMContext):
    """Yil bo'yicha qidiruv."""
    await state.set_state(SearchStates.waiting_year)
    await message.answer(
        "📅 Anime chiqarilgan yilni kiriting (masalan: 2023):",
        reply_markup=kb.cancel_kb(),
    )


@router.message(SearchStates.waiting_year)
async def search_by_year_process(message: Message, state: FSMContext):
    """Yil bo'yicha qidiruv natijalari."""
    try:
        year = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri yil kiriting (masalan: 2023).")
        return

    results = await repo.search_animes_by_year(year)
    await state.clear()

    if not results:
        await message.answer(
            f"❌ {year} yilida anime topilmadi.",
            reply_markup=kb.main_menu_kb(),
        )
        return

    await message.answer(
        f"✅ <b>{year} yilidagi {len(results)} ta anime:</b>",
        reply_markup=kb.anime_list_kb(results),
    )
    await message.answer("📋 Bosh menyu:", reply_markup=kb.main_menu_kb())


@router.message(F.text == "🔢 Kod bo'yicha")
async def search_by_code_start(message: Message, state: FSMContext):
    """Kod bo'yicha qidiruv."""
    await state.set_state(SearchStates.waiting_code)
    await message.answer(
        "🔢 Anime kodini kiriting (masalan: 101 yoki #101):",
        reply_markup=kb.cancel_kb(),
    )


@router.message(SearchStates.waiting_code)
async def search_by_code_process(message: Message, state: FSMContext):
    """Kod bo'yicha qidiruv natijasi."""
    code = message.text.strip().lstrip("#")
    await state.clear()

    anime = await repo.get_anime_by_code(code)
    if not anime:
        await message.answer(
            f"❌ #{code} kodli anime topilmadi.",
            reply_markup=kb.main_menu_kb(),
        )
        return

    await show_anime_detail(message, anime["id"])




# ==================== ANIME TAFSLOTI (INLINE CALLBACKS) ====================

@router.callback_query(F.data == "back_to_list")
async def cb_back_to_list(callback: CallbackQuery):
    """Orqaga qaytish."""
    await callback.answer()
    await callback.message.delete()


@router.callback_query(F.data.startswith("page:"))
async def cb_pagination(callback: CallbackQuery):
    """Pagination - sahifalash."""
    await callback.answer()
    # Bu yerda qayta qidiruv kerak, lekin soddalashtirish uchun
    # oxirgi natijalarni qayta ko'rsatamiz
    page = int(callback.data.split(":")[1])
    animes = await repo.get_all_animes(limit=100)
    await callback.message.edit_reply_markup(
        reply_markup=kb.anime_list_kb(animes, page=page)
    )


@router.callback_query(F.data.startswith("anime:"))
async def cb_anime_detail(callback: CallbackQuery):
    """Anime tafsilotlari sahifasi."""
    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    await show_anime_detail(callback.message, anime_id, callback=callback)


async def show_anime_detail(message_or_callback, anime_id: int, callback=None):
    """Anime tafsilotlarini ko'rsatish (umumiy funksiya)."""
    anime = await repo.get_anime_by_id(anime_id)
    if not anime:
        if callback:
            await callback.answer("Anime topilmadi.", show_alert=True)
        else:
            await message_or_callback.answer("Anime topilmadi.")
        return

    # Ko'rilganlar sonini oshirish
    await repo.increment_anime_views(anime_id)

    # Janrlarni olish
    genres = await repo.get_anime_genres(anime_id)
    genres_text = ", ".join(genres) if genres else "Ko'rsatilmagan"

    # Sevimlilarda bormi?
    is_fav = await repo.is_in_favorites(
        message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user')
        else message_or_callback.from_user.id,
        anime_id
    )

    # Epizodlar soni
    ep_count = await repo.get_episodes_count(anime_id)

    # Matn shakllantirish
    rating = anime.get("rating", 0)
    stars = "⭐" * int(rating / 2) if rating else "Baholanmagan"

    text = (
        f"🎬 <b>{anime['title']}</b>\n"
        f"{'━' * 20}\n"
    )
    if anime.get("code"):
        text += f"🔢 Kod: <b>#{anime['code']}</b>\n"
    text += (
        f"🎭 Janr: <b>{genres_text}</b>\n"
        f"📅 Yil: <b>{anime.get('release_year', 'Noma\'lum')}</b>\n"
        f"⭐ Reyting: <b>{rating}/10</b> {stars}\n"
        f"⏱ Davomiyligi: <b>{anime.get('duration', 'Noma\'lum')}</b>\n"
        f"🏢 Studiya: <b>{anime.get('studio', 'Noma\'lum')}</b>\n"
        f"📺 Qismlar: <b>{ep_count} ta</b>\n"
        f"👁 Ko'rilgan: <b>{anime.get('views', 0)} marta</b>\n"
    )
    if anime.get("description"):
        text += f"\n📝 <b>Tavsif:</b>\n{anime['description']}\n"

    # Rasm bilan yoki rasm siz
    poster_file_id = anime.get("poster_file_id")

    # Admin uchun qo'shimcha tugmalar
    viewer_id = (message_or_callback.from_user.id
                 if hasattr(message_or_callback, 'from_user')
                 else message_or_callback.from_user.id)
    is_admin_viewer = viewer_id in config.admin_ids or await repo.is_db_admin(viewer_id)

    if is_admin_viewer:
        markup = kb.anime_detail_admin_kb(anime_id, is_fav)
    else:
        markup = kb.anime_detail_kb(anime_id, is_fav)

    if poster_file_id:
        if callback:
            try:
                await callback.message.delete()
            except Exception:
                pass
        await message_or_callback.answer_photo(
            photo=poster_file_id,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        if callback:
            try:
                await callback.message.delete()
            except Exception:
                pass
        await message_or_callback.answer(
            text, reply_markup=markup, parse_mode="HTML",
        )


# ==================== EPIZODLAR ====================

@router.callback_query(F.data.startswith("episodes:"))
async def cb_episodes_list(callback: CallbackQuery):
    """Anime epizodlari ro'yxatini rasmli va oddiy xabarlarda ko'rsatish."""
    anime_id = int(callback.data.split(":")[1])
    episodes = await repo.get_episodes_by_anime(anime_id)

    if not episodes:
        await callback.answer("Hozircha qismlar yuklanmagan.", show_alert=True)
        return

    anime = await repo.get_anime_by_id(anime_id)
    title = anime.get("title", "Anime") if anime else "Anime"
    text = f"📺 <b>{title}</b> — Qismlar ro'yxati ({len(episodes)} ta):"
    markup = kb.episodes_kb(anime_id, episodes)

    try:
        # Posterli xabarda caption, postersiz oddiy xabarda text tahrirlanadi.
        if callback.message.caption is not None:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=markup,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=markup,
                parse_mode="HTML",
            )
        await callback.answer()
    except Exception:
        # Xabarni tahrirlash mumkin bo'lmasa ham tugma bosilishi javobsiz qolmasin.
        await callback.answer()
        await callback.message.answer(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("ep:"))
async def cb_send_episode(callback: CallbackQuery):
    """Epizod videosini yuborish."""
    await callback.answer()
    episode_id = int(callback.data.split(":")[1])
    episode = await repo.get_episode_by_id(episode_id)

    if not episode:
        await callback.answer("Epizod topilmadi.", show_alert=True)
        return

    anime = await repo.get_anime_by_id(episode["anime_id"])
    anime_title = anime.get("title", "Anime") if anime else "Anime"

    caption = (
        f"📺 <b>{anime_title}</b>\n"
        f"🎬 Qism {episode['episode_number']}\n"
        f"📥 Sifat: {episode.get('quality', '720p')}\n"
        f"🌐 Til: {episode.get('language', 'Uzbek')}\n"
    )
    if episode.get("title"):
        caption += f"📝 Nomi: {episode['title']}\n"

    await callback.message.answer_video(
        video=episode["video_file_id"],
        caption=caption,
        parse_mode="HTML",
    )


# ==================== SEVIMLILAR ====================

@router.callback_query(F.data.startswith("fav:"))
async def cb_add_favorite(callback: CallbackQuery):
    """Sevimlilarga qo'shish."""
    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    await repo.add_to_favorites(callback.from_user.id, anime_id)
    await callback.answer("⭐ Sevimlilarga qo'shildi!", show_alert=True)

    # Tugmalarni yangilash
    await show_anime_detail(callback.message, anime_id, callback=callback)


@router.callback_query(F.data.startswith("unfav:"))
async def cb_remove_favorite(callback: CallbackQuery):
    """Sevimlilardan olib tashlash."""
    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    await repo.remove_from_favorites(callback.from_user.id, anime_id)
    await callback.answer("❌ Sevimlilardan olib tashlandi.", show_alert=True)

    # Tugmalarni yangilash
    await show_anime_detail(callback.message, anime_id, callback=callback)


# ==================== JANR BO'YICHA QIDIRUV ====================

@router.callback_query(F.data.startswith("genre:"))
async def cb_search_by_genre(callback: CallbackQuery):
    """Janr bo'yicha anime qidiruv."""
    await callback.answer()
    parts = callback.data.split(":")
    genre_name = parts[2] if len(parts) > 2 else ""

    results = await repo.search_animes_by_genre(genre_name)
    if not results:
        await callback.message.answer(
            f"❌ \"{genre_name}\" janrida anime topilmadi."
        )
        return

    await callback.message.answer(
        f"🎭 <b>{genre_name}</b> janri bo'yicha {len(results)} ta anime:",
        reply_markup=kb.anime_list_kb(results),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    """Bo'sh callback - hech narsa qilmaslik."""
    await callback.answer()


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery):
    """Obuna tekshiruvini qayta bajarish."""
    await callback.answer("Obuna tekshirilmoqda...", show_alert=False)

    force_subs = await repo.get_force_subs()
    bot = callback.bot
    not_subscribed = []

    for sub in force_subs:
        channel_username = sub.get("channel_username", "")
        if not channel_username:
            continue
        clean_username = channel_username.lstrip("@")
        try:
            member = await bot.get_chat_member(
                chat_id=f"@{clean_username}",
                user_id=callback.from_user.id,
            )
            if member.status == "left":
                not_subscribed.append(sub)
        except Exception:
            not_subscribed.append(sub)

    if not_subscribed:
        await callback.answer(
            "⚠️ Siz hali barcha kanallarga obuna bo'lmadingiz!",
            show_alert=True,
        )
    else:
        await callback.message.delete()
        is_admin = callback.from_user.id in config.admin_ids or await repo.is_db_admin(callback.from_user.id)
        if is_admin:
            await callback.message.answer(
                "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.",
                reply_markup=kb.admin_menu_kb(),
            )
        else:
            await callback.message.answer(
                "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.",
                reply_markup=kb.main_menu_kb(),
            )
