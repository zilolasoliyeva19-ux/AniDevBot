"""
Admin handlerlari - anime qo'shish, kanalga post, statistika, broadcast.
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.dispatcher.event.bases import SkipHandler

from anime_bot.config import config
from anime_bot.database import repo
from anime_bot.keyboards import keyboards as kb
from anime_bot.states.states import (
    AddAnimeStates, BroadcastStates, ForceSubStates, AdminManageStates,
    EditAnimeStates,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Yakunlash/Bekor qilish tugmalarini yaratish uchun yordamchi funksiya
def _finish_cancel_kb() -> ReplyKeyboardBuilder:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.add(KeyboardButton(text="✅ Yakunlash"))
    kb_builder.add(KeyboardButton(text="❌ Bekor qilish"))
    return kb_builder.as_markup(resize_keyboard=True)

# Sifat tanlash inline tugmalari
def _quality_kb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text="📱 360p", callback_data="quality:360p"))
    ikb.row(InlineKeyboardButton(text="💻 720p", callback_data="quality:720p"))
    ikb.row(InlineKeyboardButton(text="🎬 1080p", callback_data="quality:1080p"))
    return ikb.as_markup()

# Til tanlash inline tugmalari
def _language_kb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text="🇺🇿 O'zbek tilida", callback_data="lang:Uzbek"))
    ikb.row(InlineKeyboardButton(text="🇷🇺 Rus tilida", callback_data="lang:Russian"))
    ikb.row(InlineKeyboardButton(text="🇯🇵 Yapon (sub)", callback_data="lang:Japanese"))
    ikb.row(InlineKeyboardButton(text="🇬🇧 Ingliz tilida", callback_data="lang:English"))
    return ikb.as_markup()

logger = logging.getLogger(__name__)
router = Router(name="admin")


async def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish (.env yoki baza)."""
    if user_id in config.admin_ids:
        return True
    return await repo.is_db_admin(user_id)


@router.message(F.text == "❌ Bekor qilish")
async def admin_cancel_early(message: Message, state: FSMContext):
    """FSM bosqichidagi bekor qilishni boshqa handlerlardan oldin ushlash."""
    if not await is_admin(message.from_user.id):
        raise SkipHandler
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_menu_kb())


# ==================== ADMIN MENYUSI ====================

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Admin panelini ochish."""
    if not await is_admin(message.from_user.id):
        await message.answer("🚫 Bu buyruq faqat adminlar uchun.")
        return

    await state.clear()
    await message.answer(
        "🔧 <b>Admin Paneli</b>\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=kb.admin_menu_kb(),
        parse_mode="HTML",
    )


@router.message(F.text == "🔙 Foydalanuvchi menyusi")
async def admin_back_to_user(message: Message, state: FSMContext):
    """Admin paneldan foydalanuvchi menyusiga qaytish."""
    await state.clear()
    await message.answer("📋 Foydalanuvchi menyusi:", reply_markup=kb.main_menu_kb())


# ==================== ANIME QO'SHISH (WIZARD) ====================

@router.message(F.text == "➕ Anime qo'shish")
async def admin_add_anime_start(message: Message, state: FSMContext):
    """Anime qo'shish wizardini boshlash."""
    if not await is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AddAnimeStates.title)
    await message.answer(
        "➕ <b>Yangi anime qo'shish</b>\n\n"
        "1️⃣ Anime nomini kiriting:",
        reply_markup=kb.cancel_kb(),
        parse_mode="HTML",
    )


# --- Step 1: Nomi ---
@router.message(AddAnimeStates.title)
async def admin_anime_title(message: Message, state: FSMContext):
    """Anime nomini saqlash."""
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("❌ Nomi juda qisqa. Qaytadan kiriting:")
        return

    await state.update_data(title=title)
    await state.set_state(AddAnimeStates.code)
    await message.answer(
        "2️⃣ Anime kodini kiriting (masalan: 101).\n"
        "Bo'sh qoldirish uchun '-' yuboring:"
    )


# --- Step 2: Kod ---
@router.message(AddAnimeStates.code)
async def admin_anime_code(message: Message, state: FSMContext):
    """Anime kodini saqlash."""
    code = message.text.strip()
    if code == "-":
        code = None
    elif len(code) > 20:
        await message.answer("❌ Kod juda uzun. Qaytadan kiriting:")
        return

    await state.update_data(code=code)
    await state.set_state(AddAnimeStates.poster)
    await message.answer(
        "3️⃣ Anime posterini rasm sifatida yuboring.\n"
        "Rasmni o'tkazib o'tish uchun '-' yuboring:"
    )


# --- Step 3: Poster ---
@router.message(AddAnimeStates.poster, F.photo)
async def admin_anime_poster_photo(message: Message, state: FSMContext):
    """Posterni file_id sifatida saqlash."""
    # Eng katta rasm sifatini olish
    poster_file_id = message.photo[-1].file_id
    await state.update_data(poster_file_id=poster_file_id)
    await state.set_state(AddAnimeStates.description)
    await message.answer("4️⃣ Anime tavsifini kiriting:")


@router.message(AddAnimeStates.poster, F.text == "-")
async def admin_anime_poster_skip(message: Message, state: FSMContext):
    """Posterni o'tkazib o'tish."""
    await state.update_data(poster_file_id=None)
    await state.set_state(AddAnimeStates.description)
    await message.answer("4️⃣ Anime tavsifini kiriting:")


# --- Step 4: Tavsif ---
@router.message(AddAnimeStates.description)
async def admin_anime_description(message: Message, state: FSMContext):
    """Tavsifni saqlash."""
    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(AddAnimeStates.rating)
    await message.answer(
        "5️⃣ Anime reytingini kiriting (0-10, masalan: 8.5):"
    )


# --- Step 5: Reyting ---
@router.message(AddAnimeStates.rating)
async def admin_anime_rating(message: Message, state: FSMContext):
    """Reytingni saqlash."""
    try:
        rating = float(message.text.strip().replace(",", "."))
        if rating < 0 or rating > 10:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, 0 dan 10 gacha bo'lgan son kiriting:")
        return

    await state.update_data(rating=rating)
    await state.set_state(AddAnimeStates.release_year)
    await message.answer("6️⃣ Anime chiqarilgan yilni kiriting (masalan: 2023):")


# --- Step 6: Yil ---
@router.message(AddAnimeStates.release_year)
async def admin_anime_year(message: Message, state: FSMContext):
    """Yilni saqlash."""
    try:
        year = int(message.text.strip())
        if year < 1900 or year > 2100:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri yil kiriting (masalan: 2023):")
        return

    await state.update_data(release_year=year)
    await state.set_state(AddAnimeStates.duration)
    await message.answer(
        "7️⃣ Anime davomiyligini kiriting (masalan: '24 epizod' yoki '24 min'):\n"
        "Bo'sh qoldirish uchun '-' yuboring:"
    )


# --- Step 7: Davomiyligi ---
@router.message(AddAnimeStates.duration)
async def admin_anime_duration(message: Message, state: FSMContext):
    """Davomiyligini saqlash."""
    duration = message.text.strip()
    if duration == "-":
        duration = None

    await state.update_data(duration=duration)
    await state.set_state(AddAnimeStates.studio)
    await message.answer(
        "8️⃣ Studiya nomini kiriting:\n"
        "Bo'sh qoldirish uchun '-' yuboring:"
    )


# --- Step 8: Studiya ---
@router.message(AddAnimeStates.studio)
async def admin_anime_studio(message: Message, state: FSMContext):
    """Studiyani saqlash va janrlar tanlashga o'tish."""
    studio = message.text.strip()
    if studio == "-":
        studio = None

    await state.update_data(studio=studio)

    # Janrlarni ko'rsatish
    genres = await repo.get_all_genres()
    if not genres:
        # Janrlar yo'q bo'lsa, o'tkazib o'tish
        await state.set_data({**await state.get_data(), "selected_genres": []})
        await state.set_state(AddAnimeStates.episodes)
        await message.answer(
            "⚠️ Janrlar mavjud emas. O'tkazib o'tilmoqda...\n\n"
            "9️⃣ Endi epizodlarni yuklashga o'tamiz.\n"
            "Birinchi epizod raqamini kiriting (masalan: 1):\n"
            "Yoki anime yaratishni yakunlash uchun '✅ Yakunlash' yuboring:",
            reply_markup=_finish_cancel_kb(),
        )
        return

    await state.update_data(selected_genres=[])
    await state.set_state(AddAnimeStates.genres)
    await message.answer(
        "9️⃣ Anime janrlarini tanlang (bir nechta tanlash mumkin):",
        reply_markup=kb.admin_genres_select_kb(genres, []),
    )


# --- Step 9: Janrlarni tanlash ---
@router.callback_query(AddAnimeStates.genres, F.data.startswith("sel_genre:"))
async def admin_select_genre(callback: CallbackQuery, state: FSMContext):
    """Janrni tanlash/olib tashlash (multi-select)."""
    await callback.answer()
    genre_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = data.get("selected_genres", [])

    if genre_id in selected:
        selected.remove(genre_id)
    else:
        selected.append(genre_id)

    await state.update_data(selected_genres=selected)
    genres = await repo.get_all_genres()
    await callback.message.edit_reply_markup(
        reply_markup=kb.admin_genres_select_kb(genres, selected)
    )


@router.callback_query(AddAnimeStates.genres, F.data == "genres_done")
async def admin_genres_done(callback: CallbackQuery, state: FSMContext):
    """Janrlar tanlashni yakunlash."""
    await callback.answer()
    data = await state.get_data()
    selected_genres = data.get("selected_genres", [])

    if not selected_genres:
        await callback.answer("⚠️ Kamida bitta janr tanlang!", show_alert=True)
        return

    # Anime ni bazaga saqlash
    anime_data = {
        "title": data.get("title"),
        "code": data.get("code"),
        "poster_file_id": data.get("poster_file_id"),
        "description": data.get("description"),
        "rating": data.get("rating", 0),
        "release_year": data.get("release_year"),
        "duration": data.get("duration"),
        "studio": data.get("studio"),
    }

    new_anime = await repo.create_anime(anime_data)
    if not new_anime:
        await callback.message.answer("❌ Anime saqlashda xatolik yuz berdi.")
        await state.clear()
        return

    anime_id = new_anime["id"]
    await repo.set_anime_genres(anime_id, selected_genres)
    await state.update_data(anime_id=anime_id)

    # Epizod yuklashga o'tish
    await state.set_state(AddAnimeStates.episode_number)
    await callback.message.answer(
        f"✅ <b>Anime saqlandi!</b> (ID: {anime_id})\n\n"
        f"📺 Endi epizodlarni yuklashga o'tamiz.\n"
        f"Epizod raqamini kiriting (masalan: 1):\n"
        f"Yoki yakunlash uchun '✅ Yakunlash' yuboring:",
        reply_markup=kb.ReplyKeyboardBuilder()
        .add(__import__("aiogram.types", fromlist=["KeyboardButton"]).KeyboardButton(text="✅ Yakunlash"))
        .add(__import__("aiogram.types", fromlist=["KeyboardButton"]).KeyboardButton(text="❌ Bekor qilish"))
        .as_markup(resize_keyboard=True),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cancel_add")
async def admin_cancel_add(callback: CallbackQuery, state: FSMContext):
    """Anime qo'shishni bekor qilish."""
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "❌ Anime qo'shish bekor qilindi.",
        reply_markup=kb.admin_menu_kb(),
    )


# --- Step 10: Epizod raqami ---
@router.message(AddAnimeStates.episode_number)
async def admin_episode_number(message: Message, state: FSMContext):
    """Epizod raqamini saqlash."""
    text = message.text.strip()

    if text == "✅ Yakunlash":
        await finish_anime_addition(message, state)
        return

    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_menu_kb())
        return

    try:
        ep_num = int(text)
        if ep_num < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri epizod raqami kiriting (masalan: 1):")
        return

    await state.update_data(episode_number=ep_num)
    await state.set_state(AddAnimeStates.episode_quality)
    await message.answer(
        f"📥 Epizod {ep_num} uchun sifatni tanlang:",
        reply_markup=_quality_kb(),
    )


@router.callback_query(AddAnimeStates.episode_quality, F.data.startswith("quality:"))
async def admin_episode_quality(callback: CallbackQuery, state: FSMContext):
    """Sifatni saqlash."""
    await callback.answer()
    quality = callback.data.split(":")[1]
    await state.update_data(quality=quality)
    await state.set_state(AddAnimeStates.episode_language)

    await callback.message.answer("🌐 Epizod tilini tanlash:", reply_markup=_language_kb())


@router.callback_query(AddAnimeStates.episode_language, F.data.startswith("lang:"))
async def admin_episode_language(callback: CallbackQuery, state: FSMContext):
    """Tilni saqlash va video kutish."""
    await callback.answer()
    language = callback.data.split(":")[1]
    await state.update_data(language=language)
    await state.set_state(AddAnimeStates.episode_video)
    await callback.message.answer(
        "📹 Endi video faylni (epizodni) yuboring.\n"
        "Video, animatsiya yoki document sifatida yuborishingiz mumkin."
    )


@router.message(AddAnimeStates.episode_video, F.video)
async def admin_episode_video(message: Message, state: FSMContext):
    """Video faylni saqlash (video sifatida)."""
    video_file_id = message.video.file_id
    await save_episode(message, state, video_file_id)


@router.message(AddAnimeStates.episode_video, F.animation)
async def admin_episode_gif(message: Message, state: FSMContext):
    """GIF animatsiyani saqlash."""
    video_file_id = message.animation.file_id
    await save_episode(message, state, video_file_id)


@router.message(AddAnimeStates.episode_video, F.document)
async def admin_episode_document(message: Message, state: FSMContext):
    """Document sifatida yuborilgan videoni saqlash."""
    if message.document.mime_type and "video" in message.document.mime_type:
        video_file_id = message.document.file_id
        await save_episode(message, state, video_file_id)
    else:
        await message.answer("❌ Iltimos, video fayl yuboring.")


async def save_episode(message: Message, state: FSMContext, video_file_id: str):
    """Epizodni bazaga saqlash va keyingi qismni so'rash."""
    data = await state.get_data()
    anime_id = data.get("anime_id")

    if not anime_id:
        await message.answer("❌ Xatolik: anime topilmadi. Qaytadan urinib ko'ring.")
        await state.clear()
        return

    episode_data = {
        "anime_id": anime_id,
        "episode_number": data.get("episode_number"),
        "quality": data.get("quality", "720p"),
        "language": data.get("language", "Uzbek"),
        "video_file_id": video_file_id,
    }

    new_ep = await repo.create_episode(episode_data)
    if not new_ep:
        await message.answer("❌ Epizod saqlashda xatolik.")
        return

    await message.answer(
        f"✅ Qism {data.get('episode_number')} saqlandi! "
        f"({data.get('quality')}, {data.get('language')})\n\n"
        f"Yana epizod qo'shish uchun raqam kiriting,\n"
        f"yoki yakunlash uchun '✅ Yakunlash' yuboring:"
    )
    await state.set_state(AddAnimeStates.episode_number)


async def finish_anime_addition(message: Message, state: FSMContext):
    """Anime qo'shishni yakunlash."""
    data = await state.get_data()
    anime_id = data.get("anime_id")
    await state.clear()

    if anime_id:
        anime = await repo.get_anime_by_id(anime_id)
        title = anime.get("title", "") if anime else ""
        ep_count = await repo.get_episodes_count(anime_id)
        await message.answer(
            f"🎉 <b>Anime muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🎬 Nomi: {title}\n"
            f"📺 Epizodlar: {ep_count} ta\n"
            f"🆔 ID: {anime_id}\n\n"
            f"📤 Kanalga post qilish uchun pastdagi tugmani bosing:",
            reply_markup=kb.post_to_channel_kb(anime_id),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "✅ Anime qo'shish yakunlandi.",
            reply_markup=kb.admin_menu_kb(),
        )


# ==================== KANALGA POST QILISH ====================

@router.callback_query(F.data.startswith("post_channel:"))
async def admin_post_to_channel(callback: CallbackQuery):
    """Animeni kanalga post qilish."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("🚫 FAQat adminlar uchun.", show_alert=True)
        return

    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    anime = await repo.get_anime_by_id(anime_id)

    if not anime:
        await callback.answer("Anime topilmadi.", show_alert=True)
        return

    if not config.post_channel:
        await callback.answer(
            "❌ Post kanali sozlanmagan. .env faylida POST_CHANNEL ni kiriting.",
            show_alert=True,
        )
        return

    # Janrlarni olish
    genres = await repo.get_anime_genres(anime_id)
    genres_text = ", ".join(genres) if genres else "Ko'rsatilmagan"
    ep_count = await repo.get_episodes_count(anime_id)

    rating = anime.get("rating", 0)
    stars = "⭐" * int(rating / 2) if rating else ""

    # Kanal uchun post matni
    post_text = (
        f"🎬 <b>{anime['title']}</b>\n"
        f"{'━' * 20}\n"
    )
    if anime.get("code"):
        post_text += f"🔢 Kod: <b>#{anime['code']}</b>\n"
    post_text += (
        f"🎭 Janr: <b>{genres_text}</b>\n"
        f"📅 Yil: <b>{anime.get('release_year', 'Noma\'lum')}</b>\n"
        f"⭐ Reyting: <b>{rating}/10</b> {stars}\n"
        f"📺 Qismlar: <b>{ep_count} ta</b>\n"
    )
    if anime.get("description"):
        desc = anime["description"]
        if len(desc) > 500:
            desc = desc[:500] + "..."
        post_text += f"\n📝 <b>Tavsif:</b>\n{desc}\n"

    post_text += f"\n🎬 Ko'rish uchun botga kiring: @{config.post_channel.replace('@', '')}"

    # Inline tugma - botga havola
    bot_username = (await callback.bot.get_me()).username
    link_kb = InlineKeyboardBuilder()
    link_kb.row(InlineKeyboardButton(
        text="▶️ Ko'rish / Yuklab olish",
        url=f"https://t.me/{bot_username}?start=anime_{anime_id}",
    ))

    poster_file_id = anime.get("poster_file_id")
    try:
        if poster_file_id:
            await callback.bot.send_photo(
                chat_id=config.post_channel,
                photo=poster_file_id,
                caption=post_text,
                parse_mode="HTML",
                reply_markup=link_kb.as_markup(),
            )
        else:
            await callback.bot.send_message(
                chat_id=config.post_channel,
                text=post_text,
                parse_mode="HTML",
                reply_markup=link_kb.as_markup(),
            )
        await callback.message.answer(
            "✅ Anime kanalga muvaffaqiyatli post qilindi!",
            reply_markup=kb.admin_menu_kb(),
        )
    except Exception as e:
        logger.error(f"Kanalga post xatolik: {e}")
        await callback.message.answer(
            f"❌ Kanalga post qilishda xatolik: {str(e)}\n"
            f"Bot kanalga admin sifatida qo'shilganligini tekshiring.",
            reply_markup=kb.admin_menu_kb(),
        )


# ==================== ANIMELAR RO'YXATI ====================

@router.message(F.text == "🎬 Animelar ro'yxati")
async def admin_anime_list(message: Message):
    """Admin uchun animelar ro'yxati."""
    if not await is_admin(message.from_user.id):
        return

    animes = await repo.get_all_animes(limit=50)
    if not animes:
        await message.answer("📭 Hozircha animelar mavjud emas.")
        return

    await message.answer(
        f"🎬 <b>Animelar ro'yxati ({len(animes)} ta):</b>",
        reply_markup=kb.anime_list_kb(animes),
        parse_mode="HTML",
    )


# ==================== STATISTIKA ====================

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    """Admin statistikasi."""
    if not await is_admin(message.from_user.id):
        return

    stats = await repo.get_stats()

    text = (
        "📊 <b>Bot Statistikasi</b>\n"
        f"{'━' * 25}\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🎬 Jami animelar: <b>{stats['total_animes']}</b>\n"
        f"📺 Jami epizodlar: <b>{stats['total_episodes']}</b>\n"
    )

    if stats.get("top_animes"):
        text += f"\n🔥 <b>Top 5 eng ko'p ko'rilgan:</b>\n"
        for i, anime in enumerate(stats["top_animes"], 1):
            views = anime.get("views", 0)
            text += f"  {i}. {anime['title']} — 👁 {views}\n"

    await message.answer(text, parse_mode="HTML")


# ==================== REKLAMA TARQATISH (BROADCAST) ====================

@router.message(F.text == "📡 Reklama tarqatish")
async def admin_broadcast_start(message: Message, state: FSMContext):
    """Broadcastni boshlash."""
    if not await is_admin(message.from_user.id):
        return

    await state.set_state(BroadcastStates.waiting_content)
    await message.answer(
        "📡 <b>Reklama tarqatish</b>\n\n"
        "Yubormoqchi bo'lgan xabarni (matn, rasm yoki video) yuboring.\n"
        "Barcha foydalanuvchilarga yuboriladi.",
        reply_markup=kb.cancel_kb(),
        parse_mode="HTML",
    )


@router.message(BroadcastStates.waiting_content)
async def admin_broadcast_send(message: Message, state: FSMContext):
    """Broadcastni barcha foydalanuvchilarga yuborish."""
    if not await is_admin(message.from_user.id):
        return

    # Barcha foydalanuvchilarni olish
    users = await repo.get_all_users()
    if not users:
        await message.answer("📭 Foydalanuvchilar yo'q.")
        await state.clear()
        return

    sent = 0
    failed = 0
    content_type = "text"

    # Progress xabar
    progress_msg = await message.answer(
        f"📡 Yuborilmoqda... 0/{len(users)}"
    )

    for i, user in enumerate(users):
        tg_user_id = user.get("tg_user_id")
        if not tg_user_id:
            continue

        try:
            if message.photo:
                content_type = "photo"
                await message.bot.send_photo(
                    chat_id=tg_user_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            elif message.video:
                content_type = "video"
                await message.bot.send_video(
                    chat_id=tg_user_id,
                    video=message.video.file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            elif message.animation:
                content_type = "animation"
                await message.bot.send_animation(
                    chat_id=tg_user_id,
                    animation=message.animation.file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            elif message.document:
                content_type = "document"
                await message.bot.send_document(
                    chat_id=tg_user_id,
                    document=message.document.file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            else:
                content_type = "text"
                await message.bot.send_message(
                    chat_id=tg_user_id,
                    text=message.text or "",
                    parse_mode="HTML",
                )
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast xato {tg_user_id}: {e}")
            failed += 1

        # Har 20 ta foydalanuvchida progressni yangilash
        if (i + 1) % 20 == 0:
            try:
                await progress_msg.edit_text(
                    f"📡 Yuborilmoqda... {i + 1}/{len(users)}"
                )
            except Exception:
                pass

    # Tarixni saqlash
    await repo.log_broadcast(message.from_user.id, content_type, sent, failed)

    await state.clear()
    await progress_msg.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"❌ Xatolik: <b>{failed}</b>\n"
        f"👥 Jami: <b>{len(users)}</b>",
        parse_mode="HTML",
    )
    await message.answer("📋 Admin menyusi:", reply_markup=kb.admin_menu_kb())


# ==================== FOYDALANUVCHILAR ====================

@router.message(F.text == "👥 Foydalanuvchilar")
async def admin_users_list(message: Message):
    """Foydalanuvchilar ro'yxati."""
    if not await is_admin(message.from_user.id):
        return

    users = await repo.get_all_users()
    if not users:
        await message.answer("📭 Foydalanuvchilar yo'q.")
        return

    text = (
        f"👥 <b>Foydalanuvchilar ({len(users)} ta):</b>\n"
        f"{'━' * 25}\n"
    )
    # Oxirgi 20 ta foydalanuvchi
    for user in users[:20]:
        name = user.get("first_name", "Noma'lum")
        uname = f" @{user['username']}" if user.get("username") else ""
        ban = " 🚫" if user.get("is_banned") else ""
        text += f"• {name}{uname}{ban}\n"

    if len(users) > 20:
        text += f"\n... va yana {len(users) - 20} ta foydalanuvchi"

    await message.answer(text, parse_mode="HTML", reply_markup=kb.admin_menu_kb())


# ==================== OBLAR KANALLARI ====================

@router.message(F.text == "📢 Obuna kanallari")
async def admin_force_sub_menu(message: Message):
    """Majburiy obuna kanallari menyusi."""
    if not await is_admin(message.from_user.id):
        return

    subs = await repo.get_force_subs()
    text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
    if subs:
        for sub in subs:
            uname = sub.get("channel_username", "Noma'lum")
            text += f"• {uname} — {sub.get('channel_url', '')}\n"
    else:
        text += "📭 Hozircha kanallar sozlanmagan.\n"

    text += "\nYangi kanal qo'shish uchun /add_sub buyrug'ini yuboring."

    await message.answer(text, parse_mode="HTML", reply_markup=kb.admin_menu_kb())


@router.message(Command("add_sub"))
async def admin_add_sub_start(message: Message, state: FSMContext):
    """Yangi majburiy obuna kanali qo'shish."""
    if not await is_admin(message.from_user.id):
        return

    await state.set_state(ForceSubStates.channel_url)
    await message.answer(
        "📢 Kanal URL manzilini kiriting (masalan: https://t.me/my_channel):",
        reply_markup=kb.cancel_kb(),
    )


@router.message(ForceSubStates.channel_url)
async def admin_add_sub_url(message: Message, state: FSMContext):
    """Kanal URL ni saqlash."""
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("❌ Iltimos, to'g'ri URL kiriting:")
        return

    await state.update_data(channel_url=url)
    await state.set_state(ForceSubStates.channel_username)
    await message.answer("Kanal username ini kiriting (masalan: @my_channel):")


@router.message(ForceSubStates.channel_username)
async def admin_add_sub_username(message: Message, state: FSMContext):
    """Kanal username ni saqlash va bazaga qo'shish."""
    username = message.text.strip()
    if not username.startswith("@"):
        username = f"@{username}"

    data = await state.get_data()
    result = await repo.add_force_sub(data["channel_url"], username)
    await state.clear()

    if result:
        await message.answer(
            f"✅ Kanal qo'shildi: {username}",
            reply_markup=kb.admin_menu_kb(),
        )
    else:
        await message.answer(
            "❌ Kanal qo'shishda xatolik.",
            reply_markup=kb.admin_menu_kb(),
        )


# ==================== ADMIN BOSHQARUVI ====================

@router.message(F.text == "🔐 Adminlar")
async def admin_manage_menu(message: Message):
    """Adminlar ro'yxati va boshqaruv."""
    if not await is_admin(message.from_user.id):
        return

    db_admins = await repo.get_all_admins()
    env_admins = config.admin_ids

    text = "🔐 <b>Adminlar ro'yxati</b>\n\n"
    text += "📋 <b>.env adminlari (doimiy):</b>\n"
    for aid in env_admins:
        text += f"  • ID: <code>{aid}</code>\n"

    text += "\n💾 <b>Baza adminlari:</b>\n"
    if db_admins:
        for admin in db_admins:
            name = admin.get("first_name") or "Noma'lum"
            uid = admin.get("tg_user_id")
            text += f"  • {name} — ID: <code>{uid}</code>\n"
    else:
        text += "  📭 Hozircha baza adminlari yo'q.\n"

    text += (
        "\n➕ Yangi admin qo'shish uchun <b>/add_admin</b> buyrug'ini yuboring.\n"
        "➖ Adminlikdan olish uchun <b>/remove_admin</b> buyrug'ini yuboring."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=kb.admin_menu_kb())


@router.message(Command("add_admin"))
async def admin_add_admin_start(message: Message, state: FSMContext):
    """Yangi admin qo'shish."""
    if not await is_admin(message.from_user.id):
        return

    await state.set_state(AdminManageStates.waiting_user_id)
    await message.answer(
        "➕ <b>Yangi admin qo'shish</b>\n\n"
        "Admin qilmoqchi bo'lgan foydalanuvchining Telegram ID sini kiriting.\n"
        "ID raqamini @userinfobot dan bilishingiz mumkin.",
        reply_markup=kb.cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AdminManageStates.waiting_user_id)
async def admin_add_admin_process(message: Message, state: FSMContext):
    """Foydalanuvchini admin qilish."""
    text = message.text.strip()
    try:
        user_id = int(text)
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri Telegram ID kiriting (faqat raqam):")
        return

    # .env admini bo'lsa, takror qo'shish shart emas
    if user_id in config.admin_ids:
        await message.answer(
            "ℹ️ Bu foydalanuvchi allaqachon .env admini sifatida ro'yxatdan o'tgan.",
            reply_markup=kb.admin_menu_kb(),
        )
        await state.clear()
        return

    # Bazada bor yoki yo'qligini tekshirish
    user = await repo.get_or_create_user(user_id)
    if not user:
        await message.answer(
            "❌ Bu ID bazada topilmadi. Foydalanuvchi avval botga kamida bir marta /start yuborgan bo'lishi kerak.",
            reply_markup=kb.admin_menu_kb(),
        )
        await state.clear()
        return

    await repo.add_admin(user_id)
    name = user.get("first_name") or "Noma'lum"
    await state.clear()
    await message.answer(
        f"✅ <b>{name}</b> (ID: <code>{user_id}</code>) admin qilindi!\n"
        f"Endi u /admin buyrug'iga kira oladi.",
        reply_markup=kb.admin_menu_kb(),
        parse_mode="HTML",
    )


@router.message(Command("remove_admin"))
async def admin_remove_admin_start(message: Message, state: FSMContext):
    """Adminlikdan olish."""
    if not await is_admin(message.from_user.id):
        return

    db_admins = await repo.get_all_admins()
    if not db_admins:
        await message.answer(
            "📭 Baza adminlari yo'q. .env adminlarini olib bo'lmaydi.",
            reply_markup=kb.admin_menu_kb(),
        )
        return

    await state.set_state(AdminManageStates.waiting_user_id)
    text = "➖ <b>Adminlikdan olish</b>\n\nHozirgi baza adminlari:\n"
    for admin in db_admins:
        name = admin.get("first_name") or "Noma'lum"
        text += f"  • {name} — ID: <code>{admin['tg_user_id']}</code>\n"
    text += "\nAdminlikdan olish uchun ID kiriting:"
    await message.answer(text, reply_markup=kb.cancel_kb(), parse_mode="HTML")


@router.message(AdminManageStates.waiting_user_id)
async def admin_remove_admin_process(message: Message, state: FSMContext):
    """Adminlikdan olish jarayoni."""
    text = message.text.strip()
    try:
        user_id = int(text)
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri Telegram ID kiriting (faqat raqam):")
        return

    if user_id in config.admin_ids:
        await message.answer(
            "⚠️ Bu foydalanuvchi .env admini — uni olib bo'lmaydi. .env faylidan o'chiring.",
            reply_markup=kb.admin_menu_kb(),
        )
        await state.clear()
        return

    is_db_admin = await repo.is_db_admin(user_id)
    if not is_db_admin:
        await message.answer(
            "❌ Bu foydalanuvchi baza admini emas.",
            reply_markup=kb.admin_menu_kb(),
        )
        await state.clear()
        return

    await repo.remove_admin(user_id)
    await state.clear()
    await message.answer(
        f"✅ Foydalanuvchi (ID: <code>{user_id}</code>) adminlikdan olindi.",
        reply_markup=kb.admin_menu_kb(),
        parse_mode="HTML",
    )


# ==================== ANIME TAHRIRLASH VA O'CHIRISH ====================

@router.callback_query(F.data.startswith("edit_anime:"))
async def admin_edit_anime_menu(callback: CallbackQuery, state: FSMContext):
    """Anime tahrirlash menyusi."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("🚫 Faqat adminlar uchun.", show_alert=True)
        return

    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    anime = await repo.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Anime topilmadi.", show_alert=True)
        return

    await state.clear()
    await state.set_state(EditAnimeStates.choosing_field)
    await state.update_data(edit_anime_id=anime_id)

    # Anime ma'lumotlarini ko'rsatish
    genres = await repo.get_anime_genres(anime_id)
    genres_text = ", ".join(genres) if genres else "Ko'rsatilmagan"
    ep_count = await repo.get_episodes_count(anime_id)

    text = (
        f"✏️ <b>Tahrirlash: {anime['title']}</b>\n\n"
        f"🔢 Kod: {anime.get('code', '-')}\n"
        f"🎭 Janr: {genres_text}\n"
        f"⭐ Reyting: {anime.get('rating', 0)}/10\n"
        f"📅 Yil: {anime.get('release_year', '-')}\n"
        f"⏱ Davomiyligi: {anime.get('duration', '-')}\n"
        f"🏢 Studiya: {anime.get('studio', '-')}\n"
        f"📺 Epizodlar: {ep_count} ta\n\n"
        f"Tahrirlamoqchi bo'lgan maydonni tanlang:"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, parse_mode="HTML",
                                  reply_markup=kb.admin_anime_edit_kb(anime_id))


@router.callback_query(EditAnimeStates.choosing_field, F.data.startswith("efield:"))
async def admin_edit_anime_field(callback: CallbackQuery, state: FSMContext):
    """Tahrirlanadigan maydonni tanlash."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("🚫 Faqat adminlar uchun.", show_alert=True)
        return

    await callback.answer()
    field = callback.data.split(":")[1]
    data = await state.get_data()
    anime_id = data.get("edit_anime_id")

    if field == "genres":
        # Janrlarni tanlash menyusi
        genres = await repo.get_all_genres()
        if not genres:
            await callback.message.answer("⚠️ Janrlar mavjud emas.")
            return

        # Hozirgi tanlangan janrlarni olish
        current_genres = await repo.get_anime_genres(anime_id)
        all_genres = await repo.get_all_genres()
        selected_ids = [g["id"] for g in all_genres if g["name"] in current_genres]

        await state.set_state(EditAnimeStates.editing_genres)
        await state.update_data(selected_genres=selected_ids)
        await callback.message.answer(
            "🎭 Janrlarni tanlang (bir nechta):",
            reply_markup=kb.admin_genres_select_kb(genres, selected_ids),
        )
        return

    if field == "episodes":
        # Epizodlarni boshqarish
        episodes = await repo.get_episodes_by_anime(anime_id)
        if not episodes:
            await callback.message.answer("📭 Bu animeda epizodlar yo'q.")
            return

        await state.set_state(EditAnimeStates.managing_episodes)
        await callback.message.answer(
            "📺 Epizodlar ro'yxati. O'chirmoqchi bo'lganini tanlang:",
            reply_markup=kb.admin_episodes_manage_kb(anime_id, episodes),
        )
        return

    if field == "poster_file_id":
        await state.set_state(EditAnimeStates.editing_value)
        await state.update_data(edit_field=field)
        await callback.message.answer(
            "🖼 Yangi posterni rasm sifatida yuboring.\n"
            "Eski posterni o'chirish uchun '-' yuboring:"
        )
        return

    field_labels = {
        "title": "yangi nomini",
        "code": "yangi kodini (yoki '-' bo'sh qoldirish uchun)",
        "description": "yangi tavsifini",
        "rating": "yangi reytingini (0-10, masalan: 8.5)",
        "release_year": "yangi yilini (masalan: 2023)",
        "duration": "yangi davomiyligini (yoki '-')",
        "studio": "yangi studiya nomini (yoki '-')",
    }

    await state.set_state(EditAnimeStates.editing_value)
    await state.update_data(edit_field=field)
    label = field_labels.get(field, "yangi qiymatini")
    await callback.message.answer(f"Anime {label} kiriting:")


@router.message(EditAnimeStates.editing_value)
async def admin_edit_anime_value(message: Message, state: FSMContext):
    """Tahrirlangan qiymatni saqlash."""
    data = await state.get_data()
    anime_id = data.get("edit_anime_id")
    field = data.get("edit_field")

    if not anime_id or not field:
        await state.clear()
        await message.answer("❌ Xatolik. Qaytadan urinib ko'ring.",
                            reply_markup=kb.admin_menu_kb())
        return

    text = message.text.strip() if message.text else ""
    value = None

    if field == "poster_file_id":
        if message.photo:
            value = message.photo[-1].file_id
        elif text == "-":
            value = None
        else:
            await message.answer("❌ Iltimos, rasm yuboring yoki '-' yuboring:")
            return
    elif field in ("title", "code", "description", "studio", "duration"):
        if text == "-" and field != "title":
            value = None
        else:
            value = text
        if field == "title" and len(value) < 2:
            await message.answer("❌ Nomi juda qisqa. Qaytadan:")
            return
    elif field == "rating":
        try:
            value = float(text.replace(",", "."))
            if value < 0 or value > 10:
                raise ValueError
        except ValueError:
            await message.answer("❌ 0-10 oralig'ida son kiriting:")
            return
    elif field == "release_year":
        try:
            value = int(text)
            if value < 1900 or value > 2100:
                raise ValueError
        except ValueError:
            await message.answer("❌ To'g'ri yil kiriting (masalan: 2023):")
            return

    await repo.update_anime_field(anime_id, field, value)

    # Tahrirlash menyusiga qaytish
    await state.set_state(EditAnimeStates.choosing_field)
    anime = await repo.get_anime_by_id(anime_id)
    await message.answer(
        f"✅ {field} yangilandi!\n\n"
        f"✏️ <b>Tahrirlash: {anime['title']}</b>\n"
        f"Tahrirlamoqchi bo'lgan maydonni tanlang:",
        reply_markup=kb.admin_anime_edit_kb(anime_id),
        parse_mode="HTML",
    )


@router.callback_query(EditAnimeStates.editing_genres, F.data.startswith("sel_genre:"))
async def admin_edit_genre_toggle(callback: CallbackQuery, state: FSMContext):
    """Tahrirlashda janr tanlash/olib tashlash."""
    await callback.answer()
    genre_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = data.get("selected_genres", [])

    if genre_id in selected:
        selected.remove(genre_id)
    else:
        selected.append(genre_id)

    await state.update_data(selected_genres=selected)
    genres = await repo.get_all_genres()
    await callback.message.edit_reply_markup(
        reply_markup=kb.admin_genres_select_kb(genres, selected)
    )


@router.callback_query(EditAnimeStates.editing_genres, F.data == "genres_done")
async def admin_edit_genres_save(callback: CallbackQuery, state: FSMContext):
    """Tahrirlangan janrlarni saqlash."""
    await callback.answer()
    data = await state.get_data()
    anime_id = data.get("edit_anime_id")
    selected = data.get("selected_genres", [])

    if not selected:
        await callback.answer("⚠️ Kamida bitta janr tanlang!", show_alert=True)
        return

    await repo.replace_anime_genres(anime_id, selected)

    # Tahrirlash menyusiga qaytish
    await state.set_state(EditAnimeStates.choosing_field)
    anime = await repo.get_anime_by_id(anime_id)
    await callback.message.answer(
        f"✅ Janrlar yangilandi!\n\n"
        f"✏️ <b>Tahrirlash: {anime['title']}</b>\n"
        f"Tahrirlamoqchi bo'lgan maydonni tanlang:",
        reply_markup=kb.admin_anime_edit_kb(anime_id),
        parse_mode="HTML",
    )


@router.callback_query(EditAnimeStates.managing_episodes, F.data.startswith("del_ep:"))
async def admin_delete_episode(callback: CallbackQuery, state: FSMContext):
    """Epizodni o'chirish."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("🚫 Faqat adminlar uchun.", show_alert=True)
        return

    await callback.answer()
    episode_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    anime_id = data.get("edit_anime_id")

    await repo.delete_episode(episode_id)

    # Epizodlar ro'yxatini yangilash
    episodes = await repo.get_episodes_by_anime(anime_id)
    if not episodes:
        await state.set_state(EditAnimeStates.choosing_field)
        await callback.message.answer(
            "✅ Epizod o'chirildi! Boshqa epizodlar yo'q.\n"
            "Tahrirlash menyusiga qaytdingiz:",
            reply_markup=kb.admin_anime_edit_kb(anime_id),
        )
        return

    await callback.message.edit_reply_markup(
        reply_markup=kb.admin_episodes_manage_kb(anime_id, episodes)
    )
    await callback.message.answer("✅ Epizod o'chirildi!")


@router.callback_query(F.data.startswith("del_anime:"))
async def admin_delete_anime_confirm(callback: CallbackQuery):
    """Anime o'chirish uchun tasdiqlash."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("🚫 Faqat adminlar uchun.", show_alert=True)
        return

    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    anime = await repo.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Anime topilmadi.", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"⚠️ <b>Diqqat!</b>\n\n"
        f"🎬 \"{anime['title']}\" animeni o'chirmoqchimisiz?\n"
        f"Bu animening barcha epizodlari, janrlari va sevimlilardan ham o'chiriladi.\n"
        f"Bu amalni qaytarib bo'lmaydi!",
        reply_markup=kb.admin_anime_delete_confirm_kb(anime_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("confirm_del_anime:"))
async def admin_delete_anime_execute(callback: CallbackQuery, state: FSMContext):
    """Animeni o'chirishni bajariish."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("🚫 Faqat adminlar uchun.", show_alert=True)
        return

    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    anime = await repo.get_anime_by_id(anime_id)
    title = anime.get("title", "Noma'lum") if anime else "Noma'lum"

    await repo.delete_anime(anime_id)
    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"✅ \"{title}\" animeni o'chirildi!",
        reply_markup=kb.admin_menu_kb(),
    )


@router.callback_query(F.data.startswith("edit_done:"))
async def admin_edit_done(callback: CallbackQuery, state: FSMContext):
    """Tahrirlashni yakunlash."""
    await callback.answer()
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "✅ Tahrirlash yakunlandi!",
        reply_markup=kb.admin_menu_kb(),
    )


@router.callback_query(F.data.startswith("edit_cancel:"))
async def admin_edit_cancel(callback: CallbackQuery, state: FSMContext):
    """Tahrirlashni bekor qilish."""
    await callback.answer()
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "❌ Tahrirlash bekor qilindi.",
        reply_markup=kb.admin_menu_kb(),
    )


@router.callback_query(F.data == "back_to_admin_list")
async def admin_back_to_anime_list(callback: CallbackQuery):
    """Admin animelar ro'yxatiga qaytish."""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    animes = await repo.get_all_animes(limit=50)
    if not animes:
        await callback.message.answer("📭 Hozircha animelar mavjud emas.",
                                     reply_markup=kb.admin_menu_kb())
        return
    await callback.message.answer(
        f"🎬 <b>Animelar ro'yxati ({len(animes)} ta):</b>",
        reply_markup=kb.anime_list_kb(animes),
        parse_mode="HTML",
    )




@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery):
    """Admin menyusiga qaytish (inline)."""
    await callback.answer()
    await callback.message.answer(
        "📋 Admin menyusi:", reply_markup=kb.admin_menu_kb()
    )
