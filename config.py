import os
from dotenv import load_dotenv

load_dotenv()

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-5-20250514"

# Instagram / Meta
INSTAGRAM_PAGE_ACCESS_TOKEN = os.getenv("INSTAGRAM_PAGE_ACCESS_TOKEN")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTONIA_TELEGRAM_CHAT_ID = os.getenv("ANTONIA_TELEGRAM_CHAT_ID")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Calendly
CALENDLY_LINK = "https://calendly.com/bloominghypnosis/15min"

# Delay settings (seconds)
MIN_DELAY = 30
MAX_DELAY = 120
EMOTIONAL_STEP_MULTIPLIER = 1.5
NIGHT_HOLD_START = 22  # 10 PM
NIGHT_HOLD_END = 8     # 8 AM
