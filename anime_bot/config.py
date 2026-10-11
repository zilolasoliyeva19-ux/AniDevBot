"""
Bot konfiguratsiyasi - .env faylidan barcha sozlamalarni o'qiydi.
SQLite ishlatiladi - Supabase ga bog'liqlik yo'q.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()


@dataclass
class Config:
    # Telegram Bot Token
    bot_token: str = os.getenv("BOT_TOKEN", "")

    # Admin Telegram user ID'lari (vergul bilan ajratilgan)
    admin_ids: list = field(default_factory=lambda: [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ])

    # Majburiy obuna kanallari (vergul bilan ajratilgan, masalan: @channel1,@channel2)
    force_sub_channels: list = field(default_factory=lambda: [
        x.strip() for x in os.getenv("FORCE_SUB_CHANNELS", "").split(",") if x.strip()
    ])

    # Post qilinadigan kanal username (masalan: @anime_channel)
    post_channel: str = os.getenv("POST_CHANNEL", "")

    @property
    def is_valid(self) -> bool:
        """Bot ishga tushishi uchun minimal sozlamalar mavjudligini tekshiradi."""
        return bool(self.bot_token)


config = Config()
