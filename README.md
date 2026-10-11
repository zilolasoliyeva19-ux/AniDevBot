# 🎬 Anime Bot - Telegram

Anime kanallari va foydalanuvchilari uchun mukammal Telegram boti.
**Python 3.11+ / aiogram 3.x / Supabase PostgreSQL**

---

## 📁 Loyiha strukturasi

```
project/
├── main.py                          # Botni ishga tushirish
├── requirements.txt                 # Python kutubxonalari
├── .env                             # Sozlamalar (tokenlar, kanallar)
├── .env.example                     # .env namunasi
└── anime_bot/
    ├── __init__.py
    ├── config.py                    # Konfiguratsiya (.env o'qish)
    ├── database/
    │   ├── __init__.py
    │   ├── connection.py            # Supabase REST API async ulanish
    │   └── repo.py                  # CRUD metodlari (users, animes, episodes...)
    ├── keyboards/
    │   ├── __init__.py
    │   └── keyboards.py             # Inline va Reply tugmalar
    ├── states/
    │   ├── __init__.py
    │   └── states.py                # FSM holatlari (wizard, broadcast)
    ├── middlewares/
    │   ├── __init__.py
    │   └── middlewares.py           # Majburiy obuna + user registratsiya
    └── handlers/
        ├── __init__.py
        ├── user.py                  # Foydalanuvchi handlerlari
        └── admin.py                 # Admin handlerlari
```

---

## 📊 Database sxemasi

Supabase PostgreSQL da 8 ta jadval:

| Jadval | Tavsif |
|--------|--------|
| `bot_users` | Foydalanuvchilar (TG ID, ism, ban status) |
| `genres` | Anime janrlari katalogi |
| `animes` | Animelar (nomi, poster, kod, reyting, yil, tavsif) |
| `anime_genres` | Anime ↔ Janr bog'lanish |
| `episodes` | Epizodlar (raqam, sifat, til, video file_id) |
| `favorites` | Sevimli animelar |
| `force_subs` | Majburiy obuna kanallari |
| `broadcast_log` | Reklama tarqatish tarixi |

---

## 🚀 Ishga tushirish

### 1. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. .env faylini sozlash

`.env` faylini oching va quyidagilarni to'ldiring:

```env
# Telegram Bot Token - @BotFather dan oling
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Admin Telegram user ID - @userinfobot dan bilishingiz mumkin
ADMIN_IDS=123456789

# Majburiy obuna kanallari (vergul bilan, bo'sh qoldirsa o'chiq)
FORCE_SUB_CHANNELS=@my_channel

# Post qilinadigan kanal (bot shu kanalga admin bo'lishi kerak)
POST_CHANNEL=@my_anime_channel
```

> **Supabase** URL va API key allaqachon `.env` da sozlangan.

### 3. Botni ishga tushirish

```bash
python main.py
```

---

## 👤 Foydalanuvchi imkoniyatlari

- **🔍 Qidirish** — Nomi, janri, yili yoki kodi bo'yicha
- **🎭 Janrlar** — Janr ro'yxatidan tanlash
- **⭐ Sevimlilar** — Yoqqan animelarni saqlash
- **🔥 Top Anime** — Eng ko'p ko'rilganlar
- **📺 Qismlar** — Har bir qismni kerakli sifat va tilde yuklab olish
- **📊 Statistika** — Bot haqida umumiy ma'lumot

## 🔧 Admin imkoniyatlari

- **➕ Anime qo'shish** — Multi-step wizard (nomi → kod → poster → tavsif → reyting → yil → davomiyligi → studiya → janrlar → epizodlar)
- **📤 Kanalga post** — Animeni bezatilgan inline tugmali formatda kanalga yuborish
- **📊 Statistika** — Foydalanuvchilar, animelar, top ko'rilganlar
- **📡 Reklama** — Barcha foydalanuvchilarga matn/rasm/video yuborish
- **👥 Foydalanuvchilar** — Ro'yxatni ko'rish
- **📢 Obuna kanallari** — Majburiy obuna kanallarini boshqarish

Admin paneliga kirish uchun: `/admin`

---

## 📝 Texnik tafsilotlar

- **Video saqlash:** Telegram serverda `file_id` orqali — xotira tejaladi
- **Majburiy obuna:** Middleware orqali har bir xabarda tekshiriladi
- **Async:** Barcha database operatsiyalari async (aiohttp + Supabase REST API)
- **FSM:** Anime qo'shish wizardi va broadcast uchun holatlar
