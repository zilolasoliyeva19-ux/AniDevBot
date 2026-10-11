/*
# Anime Bot Schema

1. New Tables
- `bot_users`: Foydalanuvchilar ro'yxati (telegram user ID, ism, username, faollik).
- `genres`: Anime janrlari katalogi.
- `animes`: Anime lar ro'yxati (nomi, poster file_id, tavsif, kodi, reyting, yil).
- `anime_genres`: Anime va janrlar orasidagi bog'lanish jadvali.
- `episodes`: Anime qismlari (qism raqami, sifat, til, video file_id).
- `favorites`: Foydalanuvchi sevimli animelari.
- `force_subs`: Majburiy obuna kanallari ro'yxati.
- `broadcast_log`: Reklama tarqatish tarixi.

2. Security
- Barcha jadvallarda RLS yoqilgan.
- Anon + authenticated CRUD ga ruxsat berilgan (bot anon key orqali ishlaydi).
*/

-- Bot foydalanuvchilari
CREATE TABLE IF NOT EXISTS bot_users (
    id BIGSERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_active TIMESTAMPTZ DEFAULT now()
);

-- Janrlar
CREATE TABLE IF NOT EXISTS genres (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Animelar
CREATE TABLE IF NOT EXISTS animes (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    title TEXT NOT NULL,
    poster_file_id TEXT,
    description TEXT,
    rating NUMERIC(3,1) DEFAULT 0,
    release_year INTEGER,
    duration TEXT,
    studio TEXT,
    status TEXT DEFAULT 'ongoing',
    views INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Anime-Janr bog'lanish
CREATE TABLE IF NOT EXISTS anime_genres (
    anime_id BIGINT NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
    genre_id BIGINT NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (anime_id, genre_id)
);

-- Epizodlar/Qismlar
CREATE TABLE IF NOT EXISTS episodes (
    id BIGSERIAL PRIMARY KEY,
    anime_id BIGINT NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
    episode_number INTEGER NOT NULL,
    title TEXT,
    quality TEXT NOT NULL DEFAULT '720p',
    language TEXT NOT NULL DEFAULT 'Uzbek',
    video_file_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Sevimlilar
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL,
    anime_id BIGINT NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (tg_user_id, anime_id)
);

-- Majburiy obuna kanallari
CREATE TABLE IF NOT EXISTS force_subs (
    id BIGSERIAL PRIMARY KEY,
    channel_url TEXT NOT NULL,
    channel_username TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Broadcast tarixi
CREATE TABLE IF NOT EXISTS broadcast_log (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    content_type TEXT NOT NULL,
    total_sent INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_animes_title ON animes(title);
CREATE INDEX IF NOT EXISTS idx_animes_code ON animes(code);
CREATE INDEX IF NOT EXISTS idx_animes_release_year ON animes(release_year);
CREATE INDEX IF NOT EXISTS idx_episodes_anime_id ON episodes(anime_id);
CREATE INDEX IF NOT EXISTS idx_favorites_tg_user ON favorites(tg_user_id);
CREATE INDEX IF NOT EXISTS idx_bot_users_tg_user_id ON bot_users(tg_user_id);

-- RLS ni yoqish
ALTER TABLE bot_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE genres ENABLE ROW LEVEL SECURITY;
ALTER TABLE animes ENABLE ROW LEVEL SECURITY;
ALTER TABLE anime_genres ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE force_subs ENABLE ROW LEVEL SECURITY;
ALTER TABLE broadcast_log ENABLE ROW LEVEL SECURITY;

-- bot_users policies
DROP POLICY IF EXISTS "anon_select_bot_users" ON bot_users;
CREATE POLICY "anon_select_bot_users" ON bot_users FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_bot_users" ON bot_users;
CREATE POLICY "anon_insert_bot_users" ON bot_users FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_bot_users" ON bot_users;
CREATE POLICY "anon_update_bot_users" ON bot_users FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_bot_users" ON bot_users;
CREATE POLICY "anon_delete_bot_users" ON bot_users FOR DELETE
    TO anon, authenticated USING (true);

-- genres policies
DROP POLICY IF EXISTS "anon_select_genres" ON genres;
CREATE POLICY "anon_select_genres" ON genres FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_genres" ON genres;
CREATE POLICY "anon_insert_genres" ON genres FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_genres" ON genres;
CREATE POLICY "anon_update_genres" ON genres FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_genres" ON genres;
CREATE POLICY "anon_delete_genres" ON genres FOR DELETE
    TO anon, authenticated USING (true);

-- animes policies
DROP POLICY IF EXISTS "anon_select_animes" ON animes;
CREATE POLICY "anon_select_animes" ON animes FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_animes" ON animes;
CREATE POLICY "anon_insert_animes" ON animes FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_animes" ON animes;
CREATE POLICY "anon_update_animes" ON animes FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_animes" ON animes;
CREATE POLICY "anon_delete_animes" ON animes FOR DELETE
    TO anon, authenticated USING (true);

-- anime_genres policies
DROP POLICY IF EXISTS "anon_select_anime_genres" ON anime_genres;
CREATE POLICY "anon_select_anime_genres" ON anime_genres FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_anime_genres" ON anime_genres;
CREATE POLICY "anon_insert_anime_genres" ON anime_genres FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_anime_genres" ON anime_genres;
CREATE POLICY "anon_delete_anime_genres" ON anime_genres FOR DELETE
    TO anon, authenticated USING (true);

-- episodes policies
DROP POLICY IF EXISTS "anon_select_episodes" ON episodes;
CREATE POLICY "anon_select_episodes" ON episodes FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_episodes" ON episodes;
CREATE POLICY "anon_insert_episodes" ON episodes FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_episodes" ON episodes;
CREATE POLICY "anon_update_episodes" ON episodes FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_episodes" ON episodes;
CREATE POLICY "anon_delete_episodes" ON episodes FOR DELETE
    TO anon, authenticated USING (true);

-- favorites policies
DROP POLICY IF EXISTS "anon_select_favorites" ON favorites;
CREATE POLICY "anon_select_favorites" ON favorites FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_favorites" ON favorites;
CREATE POLICY "anon_insert_favorites" ON favorites FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_favorites" ON favorites;
CREATE POLICY "anon_delete_favorites" ON favorites FOR DELETE
    TO anon, authenticated USING (true);

-- force_subs policies
DROP POLICY IF EXISTS "anon_select_force_subs" ON force_subs;
CREATE POLICY "anon_select_force_subs" ON force_subs FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_force_subs" ON force_subs;
CREATE POLICY "anon_insert_force_subs" ON force_subs FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_force_subs" ON force_subs;
CREATE POLICY "anon_delete_force_subs" ON force_subs FOR DELETE
    TO anon, authenticated USING (true);

-- broadcast_log policies
DROP POLICY IF EXISTS "anon_select_broadcast_log" ON broadcast_log;
CREATE POLICY "anon_select_broadcast_log" ON broadcast_log FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_broadcast_log" ON broadcast_log;
CREATE POLICY "anon_insert_broadcast_log" ON broadcast_log FOR INSERT
    TO anon, authenticated WITH CHECK (true);

-- Boshlang'ich janrlar
INSERT INTO genres (name) VALUES
    ('Action'), ('Adventure'), ('Comedy'), ('Drama'), ('Fantasy'),
    ('Horror'), ('Mystery'), ('Romance'), ('Sci-Fi'), ('Slice of Life'),
    ('Sports'), ('Supernatural'), ('Thriller'), ('Shounen'), ('Shoujo')
ON CONFLICT (name) DO NOTHING;