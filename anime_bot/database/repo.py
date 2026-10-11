"""
Database repo - har bir jadval uchun qulay CRUD metodlari.
Barcha metodlar async va SQLite (aiosqlite) orqali ishlaydi.
"""
from typing import Optional
from anime_bot.database.connection import db, init_db


# ==================== INIT ====================

async def setup_database():
    """Bot ishga tushganda jadvallarni yaratish."""
    await init_db()


# ==================== USERS ====================

async def get_or_create_user(tg_user_id: int, first_name: str = None,
                              last_name: str = None, username: str = None) -> dict:
    """Foydalanuvchini bazadan topadi yoki yangi yaratadi."""
    user = await db.fetchone(
        "SELECT * FROM bot_users WHERE tg_user_id = ?", (tg_user_id,)
    )
    if user:
        await db.execute(
            "UPDATE bot_users SET last_active = datetime('now') WHERE tg_user_id = ?",
            (tg_user_id,)
        )
        return user
    await db.execute(
        "INSERT OR IGNORE INTO bot_users (tg_user_id, first_name, last_name, username) VALUES (?, ?, ?, ?)",
        (tg_user_id, first_name, last_name, username)
    )
    return await db.fetchone(
        "SELECT * FROM bot_users WHERE tg_user_id = ?", (tg_user_id,)
    )


async def is_user_banned(tg_user_id: int) -> bool:
    user = await db.fetchone(
        "SELECT is_banned FROM bot_users WHERE tg_user_id = ?", (tg_user_id,)
    )
    return bool(user["is_banned"]) if user else False


async def ban_user(tg_user_id: int) -> bool:
    await db.execute(
        "UPDATE bot_users SET is_banned = 1 WHERE tg_user_id = ?", (tg_user_id,)
    )
    return True


async def unban_user(tg_user_id: int) -> bool:
    await db.execute(
        "UPDATE bot_users SET is_banned = 0 WHERE tg_user_id = ?", (tg_user_id,)
    )
    return True


async def get_all_users() -> list[dict]:
    return await db.fetchall("SELECT * FROM bot_users ORDER BY created_at DESC")


async def get_user_count() -> int:
    result = await db.fetchone("SELECT COUNT(*) as cnt FROM bot_users")
    return result["cnt"] if result else 0


# ==================== ADMINS ====================

async def get_all_admins() -> list[dict]:
    """Baza adminlari ro'yxati."""
    return await db.fetchall(
        "SELECT * FROM bot_users WHERE is_admin = 1 ORDER BY created_at ASC"
    )


async def add_admin(tg_user_id: int) -> bool:
    """Foydalanuvchini admin qilish."""
    await db.execute(
        "UPDATE bot_users SET is_admin = 1 WHERE tg_user_id = ?", (tg_user_id,)
    )
    return True


async def remove_admin(tg_user_id: int) -> bool:
    """Adminlikdan olish."""
    await db.execute(
        "UPDATE bot_users SET is_admin = 0 WHERE tg_user_id = ?", (tg_user_id,)
    )
    return True


async def is_db_admin(tg_user_id: int) -> bool:
    """Foydalanuvchi bazada admin ekanligini tekshirish."""
    user = await db.fetchone(
        "SELECT is_admin FROM bot_users WHERE tg_user_id = ?", (tg_user_id,)
    )
    return bool(user["is_admin"]) if user else False


# ==================== GENRES ====================

async def get_all_genres() -> list[dict]:
    return await db.fetchall("SELECT * FROM genres ORDER BY name ASC")


async def get_genre_by_name(name: str) -> Optional[dict]:
    return await db.fetchone("SELECT * FROM genres WHERE name = ?", (name,))


async def create_genre(name: str) -> Optional[dict]:
    rowid = await db.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (name,))
    if rowid:
        return await db.fetchone("SELECT * FROM genres WHERE name = ?", (name,))
    return None


# ==================== ANIMES ====================

async def create_anime(data: dict) -> Optional[dict]:
    rowid = await db.execute(
        """INSERT INTO animes (code, title, poster_file_id, description, rating,
           release_year, duration, studio, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (data.get("code"), data.get("title"), data.get("poster_file_id"),
         data.get("description"), data.get("rating", 0), data.get("release_year"),
         data.get("duration"), data.get("studio"), data.get("status", "ongoing"))
    )
    if rowid:
        return await db.fetchone("SELECT * FROM animes WHERE id = ?", (rowid,))
    return None


async def get_anime_by_id(anime_id: int) -> Optional[dict]:
    return await db.fetchone("SELECT * FROM animes WHERE id = ?", (anime_id,))


async def get_anime_by_code(code: str) -> Optional[dict]:
    return await db.fetchone("SELECT * FROM animes WHERE code = ?", (code,))


async def get_all_animes(limit: int = 50, offset: int = 0) -> list[dict]:
    return await db.fetchall(
        "SELECT * FROM animes ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )


async def search_animes_by_title(title: str) -> list[dict]:
    return await db.fetchall(
        "SELECT * FROM animes WHERE title LIKE ? ORDER BY title ASC",
        (f"%{title}%",)
    )


async def search_animes_by_year(year: int) -> list[dict]:
    return await db.fetchall(
        "SELECT * FROM animes WHERE release_year = ? ORDER BY title ASC",
        (year,)
    )


async def search_animes_by_genre(genre_name: str) -> list[dict]:
    return await db.fetchall(
        """SELECT a.* FROM animes a
           INNER JOIN anime_genres ag ON a.id = ag.anime_id
           INNER JOIN genres g ON ag.genre_id = g.id
           WHERE g.name = ? ORDER BY a.title ASC""",
        (genre_name,)
    )


async def increment_anime_views(anime_id: int):
    await db.execute(
        "UPDATE animes SET views = views + 1 WHERE id = ?", (anime_id,)
    )


async def get_top_animes(limit: int = 10) -> list[dict]:
    return await db.fetchall(
        "SELECT * FROM animes ORDER BY views DESC LIMIT ?", (limit,)
    )


async def get_anime_genres(anime_id: int) -> list[str]:
    rows = await db.fetchall(
        """SELECT g.name FROM genres g
           INNER JOIN anime_genres ag ON g.id = ag.genre_id
           WHERE ag.anime_id = ?""",
        (anime_id,)
    )
    return [row["name"] for row in rows]


async def set_anime_genres(anime_id: int, genre_ids: list[int]):
    for gid in genre_ids:
        await db.execute(
            "INSERT OR IGNORE INTO anime_genres (anime_id, genre_id) VALUES (?, ?)",
            (anime_id, gid)
        )


async def update_anime_field(anime_id: int, field: str, value):
    """Animening bitta maydonini yangilash."""
    allowed = ("title", "code", "poster_file_id", "description",
               "rating", "release_year", "duration", "studio", "status")
    if field not in allowed:
        return False
    await db.execute(
        f"UPDATE animes SET {field} = ? WHERE id = ?", (value, anime_id)
    )
    return True


async def delete_anime(anime_id: int) -> bool:
    """Animeni va unga bog'liq epizodlar, janrlar, sevimlilarni o'chirish."""
    await db.execute("DELETE FROM episodes WHERE anime_id = ?", (anime_id,))
    await db.execute("DELETE FROM anime_genres WHERE anime_id = ?", (anime_id,))
    await db.execute("DELETE FROM favorites WHERE anime_id = ?", (anime_id,))
    await db.execute("DELETE FROM animes WHERE id = ?", (anime_id,))
    return True


async def replace_anime_genres(anime_id: int, genre_ids: list[int]):
    """Animening janrlarini to'liq almashtirish."""
    await db.execute("DELETE FROM anime_genres WHERE anime_id = ?", (anime_id,))
    for gid in genre_ids:
        await db.execute(
            "INSERT OR IGNORE INTO anime_genres (anime_id, genre_id) VALUES (?, ?)",
            (anime_id, gid)
        )


# ==================== EPISODES ====================

async def create_episode(data: dict) -> Optional[dict]:
    rowid = await db.execute(
        """INSERT INTO episodes (anime_id, episode_number, title, quality, language, video_file_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (data["anime_id"], data["episode_number"], data.get("title"),
         data.get("quality", "720p"), data.get("language", "Uzbek"),
         data["video_file_id"])
    )
    if rowid:
        return await db.fetchone("SELECT * FROM episodes WHERE id = ?", (rowid,))
    return None


async def get_episodes_by_anime(anime_id: int) -> list[dict]:
    return await db.fetchall(
        "SELECT * FROM episodes WHERE anime_id = ? ORDER BY episode_number ASC",
        (anime_id,)
    )


async def get_episode(anime_id: int, episode_number: int, quality: str = None) -> Optional[dict]:
    if quality:
        return await db.fetchone(
            "SELECT * FROM episodes WHERE anime_id = ? AND episode_number = ? AND quality = ?",
            (anime_id, episode_number, quality)
        )
    return await db.fetchone(
        "SELECT * FROM episodes WHERE anime_id = ? AND episode_number = ?",
        (anime_id, episode_number)
    )


async def get_episode_by_id(episode_id: int) -> Optional[dict]:
    return await db.fetchone("SELECT * FROM episodes WHERE id = ?", (episode_id,))


async def get_episodes_count(anime_id: int) -> int:
    result = await db.fetchone(
        "SELECT COUNT(*) as cnt FROM episodes WHERE anime_id = ?", (anime_id,)
    )
    return result["cnt"] if result else 0


async def delete_episode(episode_id: int) -> bool:
    """Epizodni o'chirish."""
    await db.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
    return True


# ==================== FAVORITES ====================

async def add_to_favorites(tg_user_id: int, anime_id: int) -> bool:
    try:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (tg_user_id, anime_id) VALUES (?, ?)",
            (tg_user_id, anime_id)
        )
        return True
    except Exception:
        return False


async def remove_from_favorites(tg_user_id: int, anime_id: int) -> bool:
    await db.execute(
        "DELETE FROM favorites WHERE tg_user_id = ? AND anime_id = ?",
        (tg_user_id, anime_id)
    )
    return True


async def is_in_favorites(tg_user_id: int, anime_id: int) -> bool:
    result = await db.fetchone(
        "SELECT id FROM favorites WHERE tg_user_id = ? AND anime_id = ?",
        (tg_user_id, anime_id)
    )
    return result is not None


async def get_user_favorites(tg_user_id: int) -> list[dict]:
    return await db.fetchall(
        """SELECT a.* FROM animes a
           INNER JOIN favorites f ON a.id = f.anime_id
           WHERE f.tg_user_id = ? ORDER BY f.created_at DESC""",
        (tg_user_id,)
    )


# ==================== FORCE SUBS ====================

async def get_force_subs() -> list[dict]:
    return await db.fetchall("SELECT * FROM force_subs WHERE is_active = 1")


async def add_force_sub(channel_url: str, channel_username: str = None) -> Optional[dict]:
    rowid = await db.execute(
        "INSERT INTO force_subs (channel_url, channel_username) VALUES (?, ?)",
        (channel_url, channel_username)
    )
    if rowid:
        return await db.fetchone("SELECT * FROM force_subs WHERE id = ?", (rowid,))
    return None


async def remove_force_sub(sub_id: int) -> bool:
    await db.execute("DELETE FROM force_subs WHERE id = ?", (sub_id,))
    return True


# ==================== BROADCAST ====================

async def log_broadcast(admin_id: int, content_type: str,
                        sent: int, failed: int) -> Optional[dict]:
    rowid = await db.execute(
        "INSERT INTO broadcast_log (admin_id, content_type, total_sent, total_failed) VALUES (?, ?, ?, ?)",
        (admin_id, content_type, sent, failed)
    )
    if rowid:
        return await db.fetchone("SELECT * FROM broadcast_log WHERE id = ?", (rowid,))
    return None


# ==================== STATISTICS ====================

async def get_stats() -> dict:
    users = await db.fetchone("SELECT COUNT(*) as cnt FROM bot_users")
    animes = await db.fetchone("SELECT COUNT(*) as cnt FROM animes")
    episodes = await db.fetchone("SELECT COUNT(*) as cnt FROM episodes")
    top = await get_top_animes(5)
    return {
        "total_users": users["cnt"] if users else 0,
        "total_animes": animes["cnt"] if animes else 0,
        "total_episodes": episodes["cnt"] if episodes else 0,
        "top_animes": top,
    }
