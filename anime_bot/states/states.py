"""
FSM States - Admin anime qo'shish wizardi va broadcast uchun holatlar.
"""
from aiogram.fsm.state import State, StatesGroup


class AddAnimeStates(StatesGroup):
    """Anime qo'shish wizardining bosqichlari."""
    title = State()           # Anime nomi
    code = State()            # Anime kodi (masalan #101)
    poster = State()          # Poster/rasm (file_id)
    description = State()     # Tavsif
    rating = State()          # Reyting
    release_year = State()    # Chiqarilgan yil
    duration = State()        # Davomiyligi
    studio = State()          # Studiya
    genres = State()          # Janrlarni tanlash
    episodes = State()        # Epizodlarni yuklash
    episode_number = State()  # Epizod raqami
    episode_quality = State() # Epizod sifati
    episode_language = State() # Epizod tili
    episode_video = State()   # Epizod video fayli


class BroadcastStates(StatesGroup):
    """Reklama tarqatish holatlari."""
    waiting_content = State()  # Matn/rasm/video kutish
    confirming = State()       # Tasdiqlash


class ForceSubStates(StatesGroup):
    """Majburiy obuna kanali qo'shish."""
    channel_url = State()       # Kanal URL
    channel_username = State()  # Kanal username


class SearchStates(StatesGroup):
    """Qidiruv holatlari."""
    waiting_title = State()  # Nomi bo'yicha
    waiting_year = State()   # Yil bo'yicha
    waiting_code = State()   # Kod bo'yicha


class AdminManageStates(StatesGroup):
    """Admin boshqaruvi holatlari."""
    waiting_user_id = State()  # Admin qilinadigan foydalanuvchi ID si


class EditAnimeStates(StatesGroup):
    """Anime tahrirlash holatlari."""
    choosing_field = State()   # Qaysi maydonni tahrirlashni tanlash
    editing_value = State()    # Yangi qiymatni kutish
    editing_genres = State()   # Janrlarni tanlash
    managing_episodes = State()  # Epizodlarni boshqarish
