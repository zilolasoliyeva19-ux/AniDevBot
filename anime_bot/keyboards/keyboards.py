"""
Inline va Reply tugmalar - foydalanuvchi va admin uchun.
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ==================== REPLY KEYBOARDS (FOYDALANUVCHI) ====================

def main_menu_kb() -> ReplyKeyboardMarkup:
    """Bosh menyu - foydalanuvchi uchun asosiy tugmalar."""
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🔍 Qidirish"))
    kb.row(
        KeyboardButton(text="🎭 Janrlar"),
        KeyboardButton(text="⭐ Sevimlilar"),
    )
    kb.row(
        KeyboardButton(text="🔥 Top Anime"),
        KeyboardButton(text="📊 Statistika"),
    )
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def search_menu_kb() -> ReplyKeyboardMarkup:
    """Qidiruv turlari menyusi."""
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="📖 Nomi bo'yicha"))
    kb.row(
        KeyboardButton(text="🎭 Janr bo'yicha"),
        KeyboardButton(text="📅 Yil bo'yicha"),
    )
    kb.row(KeyboardButton(text="🔢 Kod bo'yicha"))
    kb.row(KeyboardButton(text="🔙 Bosh menyu"))
    return kb.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi."""
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="❌ Bekor qilish"))
    return kb.as_markup(resize_keyboard=True)


def back_to_main_kb() -> ReplyKeyboardMarkup:
    """Bosh menyuga qaytish."""
    return main_menu_kb()


# ==================== REPLY KEYBOARDS (ADMIN) ====================

def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Admin bosh menyusi."""
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="➕ Anime qo'shish"))
    kb.row(
        KeyboardButton(text="📤 Kanalga post"),
        KeyboardButton(text="📊 Statistika"),
    )
    kb.row(
        KeyboardButton(text="📡 Reklama tarqatish"),
        KeyboardButton(text="🎬 Animelar ro'yxati"),
    )
    kb.row(
        KeyboardButton(text="👥 Foydalanuvchilar"),
        KeyboardButton(text="📢 Obuna kanallari"),
    )
    kb.row(KeyboardButton(text="🔐 Adminlar"))
    kb.row(KeyboardButton(text="🔙 Foydalanuvchi menyusi"))
    return kb.as_markup(resize_keyboard=True)


# ==================== INLINE KEYBOARDS ====================

def anime_list_kb(animes: list[dict], page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    """Anime ro'yxati uchun inline tugmalar (pagination bilan)."""
    kb = InlineKeyboardBuilder()
    start = page * per_page
    end = start + per_page
    page_animes = animes[start:end]

    for anime in page_animes:
        title = anime.get("title", "Noma'lum")
        code = anime.get("code", "")
        rating = anime.get("rating", 0)
        btn_text = f"🎬 {title}"
        if code:
            btn_text += f" | {code}"
        if rating:
            btn_text += f" | ⭐{rating}"
        kb.row(InlineKeyboardButton(
            text=btn_text,
            callback_data=f"anime:{anime['id']}",
        ))

    # Pagination tugmalari
    total_pages = (len(animes) + per_page - 1) // per_page
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"page:{page - 1}",
            ))
        nav_buttons.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="noop",
        ))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"page:{page + 1}",
            ))
        kb.row(*nav_buttons)

    return kb.as_markup()


def anime_detail_kb(anime_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Anime tafsilotlari sahifasi uchun tugmalar."""
    kb = InlineKeyboardBuilder()

    # Epizodlarni ko'rish
    kb.row(InlineKeyboardButton(
        text="📺 Qismlarni ko'rish",
        callback_data=f"episodes:{anime_id}",
    ))

    # Sevimlilarga qo'shish / olib tashlash
    if is_favorite:
        kb.row(InlineKeyboardButton(
            text="❌ Sevimlilardan olib tashlash",
            callback_data=f"unfav:{anime_id}",
        ))
    else:
        kb.row(InlineKeyboardButton(
            text="⭐ Sevimlilarga qo'shish",
            callback_data=f"fav:{anime_id}",
        ))

    # Orqaga qaytish
    kb.row(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="back_to_list",
    ))

    return kb.as_markup()


def anime_detail_admin_kb(anime_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Anime tafsilotlari - admin uchun (tahrirlash/o'chirish tugmalari bilan)."""
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(
        text="📺 Qismlarni ko'rish",
        callback_data=f"episodes:{anime_id}",
    ))

    if is_favorite:
        kb.row(InlineKeyboardButton(
            text="❌ Sevimlilardan olib tashlash",
            callback_data=f"unfav:{anime_id}",
        ))
    else:
        kb.row(InlineKeyboardButton(
            text="⭐ Sevimlilarga qo'shish",
            callback_data=f"fav:{anime_id}",
        ))

    kb.row(InlineKeyboardButton(
        text="✏️ Tahrirlash",
        callback_data=f"edit_anime:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="🗑 O'chirish",
        callback_data=f"del_anime:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="back_to_list",
    ))

    return kb.as_markup()


def episodes_kb(anime_id: int, episodes: list[dict]) -> InlineKeyboardMarkup:
    """Epizodlar ro'yxati uchun tugmalar."""
    kb = InlineKeyboardBuilder()

    # Sifat bo'yicha guruhlash
    qualities_seen = set()
    for ep in episodes:
        ep_num = ep.get("episode_number", 0)
        quality = ep.get("quality", "720p")
        lang = ep.get("language", "Uzbek")
        btn_text = f"Qism {ep_num} | {quality} | {lang}"
        kb.row(InlineKeyboardButton(
            text=btn_text,
            callback_data=f"ep:{ep['id']}",
        ))

    kb.row(InlineKeyboardButton(
        text="🔙 Anime sahifasiga",
        callback_data=f"anime:{anime_id}",
    ))

    return kb.as_markup()


def genres_kb(genres: list[dict]) -> InlineKeyboardMarkup:
    """Janrlar ro'yxati uchun inline tugmalar."""
    kb = InlineKeyboardBuilder()
    for genre in genres:
        kb.row(InlineKeyboardButton(
            text=f"🎭 {genre['name']}",
            callback_data=f"genre:{genre['id']}:{genre['name']}",
        ))
    return kb.as_markup()


def confirm_kb(action: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Tasdiqlash tugmasi."""
    kb = InlineKeyboardBuilder()
    data = f"confirm:{action}" if item_id is None else f"confirm:{action}:{item_id}"
    kb.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=data))
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return kb.as_markup()


def post_to_channel_kb(anime_id: int) -> InlineKeyboardMarkup:
    """Kanalga post qilish uchun tugma (admin)."""
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="📤 Kanalga post qilish",
        callback_data=f"post_channel:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="🔙 Admin menyusi",
        callback_data="admin_back",
    ))
    return kb.as_markup()


def force_sub_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    """Majburiy obuna kanallari uchun tugmalar."""
    kb = InlineKeyboardBuilder()
    for ch in channels:
        url = ch.get("channel_url", "")
        username = ch.get("channel_username", "Kanal")
        if url:
            kb.row(InlineKeyboardButton(
                text=f"📢 {username}",
                url=url,
            ))

    # Kanal egasi botni tanlab, kanalga administrator qilib qo'shishi mumkin.
    # Telegram ochadigan tanlash oynasida kerakli kanalni tanlash lozim.
    kb.row(InlineKeyboardButton(
        text="➕ Botni kanalga admin qilish",
        url="https://t.me/AniDevwBot?startchannel&admin=post_messages+edit_messages+invite_users",
    ))
    kb.row(InlineKeyboardButton(
        text="✅ Obuna bo'ldim — tekshirish",
        callback_data="check_sub",
    ))
    return kb.as_markup()


def admin_genres_select_kb(genres: list[dict], selected: list[int] = None) -> InlineKeyboardMarkup:
    """Admin anime qo'shishda janrlarni tanlash uchun (multi-select)."""
    kb = InlineKeyboardBuilder()
    selected = selected or []
    for genre in genres:
        prefix = "✅ " if genre["id"] in selected else "⬜ "
        kb.row(InlineKeyboardButton(
            text=f"{prefix}{genre['name']}",
            callback_data=f"sel_genre:{genre['id']}",
        ))
    kb.row(InlineKeyboardButton(
        text="✅ Tasdiqlash",
        callback_data="genres_done",
    ))
    kb.row(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data="cancel_add",
    ))
    return kb.as_markup()


def admin_anime_manage_kb(anime_id: int) -> InlineKeyboardMarkup:
    """Admin uchun anime boshqaruvi tugmalari (tahrirlash/o'chirish)."""
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✏️ Tahrirlash",
        callback_data=f"edit_anime:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="🗑 O'chirish",
        callback_data=f"del_anime:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="📤 Kanalga post",
        callback_data=f"post_channel:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="🔙 Animelar ro'yxati",
        callback_data="back_to_admin_list",
    ))
    return kb.as_markup()


def admin_anime_edit_kb(anime_id: int) -> InlineKeyboardMarkup:
    """Anime tahrirlash - maydon tanlash tugmalari."""
    kb = InlineKeyboardBuilder()
    fields = [
        ("🎬 Nomi", "efield:title"),
        ("🔢 Kodi", "efield:code"),
        ("📝 Tavsifi", "efield:description"),
        ("⭐ Reytingi", "efield:rating"),
        ("📅 Yili", "efield:release_year"),
        ("⏱ Davomiyligi", "efield:duration"),
        ("🏢 Studiya", "efield:studio"),
        ("🖼 Poster", "efield:poster_file_id"),
        ("🎭 Janrlar", "efield:genres"),
        ("📺 Epizodlar", "efield:episodes"),
    ]
    for label, cb in fields:
        kb.row(InlineKeyboardButton(text=label, callback_data=cb))
    kb.row(InlineKeyboardButton(
        text="✅ Yakunlandi",
        callback_data=f"edit_done:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data=f"edit_cancel:{anime_id}",
    ))
    return kb.as_markup()


def admin_anime_delete_confirm_kb(anime_id: int) -> InlineKeyboardMarkup:
    """Anime o'chirishni tasdiqlash tugmasi."""
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✅ Ha, o'chirish",
        callback_data=f"confirm_del_anime:{anime_id}",
    ))
    kb.row(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data=f"edit_cancel:{anime_id}",
    ))
    return kb.as_markup()


def admin_episodes_manage_kb(anime_id: int, episodes: list[dict]) -> InlineKeyboardMarkup:
    """Admin uchun epizodlarni boshqarish (o'chirish)."""
    kb = InlineKeyboardBuilder()
    for ep in episodes:
        btn_text = f"🗑 Qism {ep['episode_number']} | {ep.get('quality', '')} | {ep.get('language', '')}"
        kb.row(InlineKeyboardButton(
            text=btn_text,
            callback_data=f"del_ep:{ep['id']}",
        ))
    kb.row(InlineKeyboardButton(
        text="🔙 Tahrirlash menyusi",
        callback_data=f"edit_anime:{anime_id}",
    ))
    return kb.as_markup()
