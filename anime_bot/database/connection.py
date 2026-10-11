"""
SQLite async database ulanish moduli - aiosqlite yordamida.
Bot ma'lumotlarini SQLite faylida saqlaydi.
"""
import aiosqlite
from typing import Any, Optional
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "anime_bot.db")


async def init_db():
    """Baza jadvallarini yaratish (bot ishga tushganda chaqiriladi)."""
    db = await aiosqlite.connect(DB_PATH)
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS bot_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER NOT NULL UNIQUE,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            is_admin INTEGER NOT NULL DEFAULT 0,
            is_banned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            last_active TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS animes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            title TEXT NOT NULL,
            poster_file_id TEXT,
            description TEXT,
            rating REAL DEFAULT 0,
            release_year INTEGER,
            duration TEXT,
            studio TEXT,
            status TEXT DEFAULT 'ongoing',
            views INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS anime_genres (
            anime_id INTEGER NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
            genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
            PRIMARY KEY (anime_id, genre_id)
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
            episode_number INTEGER NOT NULL,
            title TEXT,
            quality TEXT NOT NULL DEFAULT '720p',
            language TEXT NOT NULL DEFAULT 'Uzbek',
            video_file_id TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER NOT NULL,
            anime_id INTEGER NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE (tg_user_id, anime_id)
        );

        CREATE TABLE IF NOT EXISTS force_subs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT NOT NULL,
            channel_username TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS broadcast_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            total_sent INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_animes_title ON animes(title);
        CREATE INDEX IF NOT EXISTS idx_animes_code ON animes(code);
        CREATE INDEX IF NOT EXISTS idx_episodes_anime_id ON episodes(anime_id);
        CREATE INDEX IF NOT EXISTS idx_favorites_tg_user ON favorites(tg_user_id);
    """)

    # Boshlang'ich janrlar (faqat birinchi marta)
    cursor = await db.execute("SELECT COUNT(*) FROM genres")
    count = await cursor.fetchone()
    await cursor.close()
    if count[0] == 0:
        genres = [
            'Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy',
            'Horror', 'Mystery', 'Romance', 'Sci-Fi', 'Slice of Life',
            'Sports', 'Supernatural', 'Thriller', 'Shounen', 'Shoujo'
        ]
        for g in genres:
            await db.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g,))
        await db.commit()

    await db.commit()
    await db.close()


class Database:
    """SQLite async wrapper - aiosqlite ustida qulay CRUD metodlari."""

    async def _get(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(DB_PATH)
        conn.row_factory = aiosqlite.Row
        return conn

    # ==================== GENERIC CRUD ====================

    async def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """SELECT - barcha qatorlarni dict ko'rinishida qaytaradi."""
        conn = await self._get()
        try:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    async def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """SELECT - bitta qatorni dict ko'rinishida qaytaradi."""
        conn = await self._get()
        try:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            await cursor.close()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def execute(self, query: str, params: tuple = ()) -> int:
        """INSERT/UPDATE/DELETE - so'rovni bajaradi va lastrowid qaytaradi."""
        conn = await self._get()
        try:
            cursor = await conn.execute(query, params)
            await conn.commit()
            rowid = cursor.lastrowid
            await cursor.close()
            return rowid
        finally:
            await conn.close()


db = Database()
