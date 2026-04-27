import os
from dotenv import load_dotenv

load_dotenv()

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Instagram / Meta
INSTAGRAM_PAGE_ACCESS_TOKEN = os.getenv("INSTAGRAM_PAGE_ACCESS_TOKEN")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN")
INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID", "")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Booking link — URL the bot sends at the end of the script. Set via env.
BOOKING_LINK = os.getenv("BOOKING_LINK", "")

# Delay settings (seconds)
MIN_DELAY = 30
MAX_DELAY = 120
EMOTIONAL_STEP_MULTIPLIER = 1.5
NIGHT_HOLD_START = 22  # 10 PM
NIGHT_HOLD_END = 8     # 8 AM
