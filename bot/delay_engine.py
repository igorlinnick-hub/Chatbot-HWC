from datetime import datetime
from config import (
    MIN_DELAY,
    MAX_DELAY,
    EMOTIONAL_STEP_MULTIPLIER,
    NIGHT_HOLD_START,
    NIGHT_HOLD_END,
)
from prompts.steps import CONVERSATION_STEPS

# Map emotional weight strings to multipliers
WEIGHT_MULTIPLIERS = {
    "low": 1.0,
    "medium": 1.3,
    "high": EMOTIONAL_STEP_MULTIPLIER,
}


def calculate_delay(message_length: int, step: int) -> int:
    """
    Calculate response delay in seconds based on message length and step.
    Uses emotional_weight from step data instead of hardcoded set.
    """
    # Base delay scales with message length
    base = min(MIN_DELAY + (message_length // 20) * 5, MAX_DELAY)

    # Apply emotional weight multiplier from step data
    step_data = CONVERSATION_STEPS.get(step, {})
    weight = step_data.get("emotional_weight", "low")
    multiplier = WEIGHT_MULTIPLIERS.get(weight, 1.0)
    base = int(base * multiplier)

    return min(base, MAX_DELAY)


def is_night_hours() -> bool:
    """Check if current time is in the night hold window."""
    hour = datetime.now().hour
    if NIGHT_HOLD_START > NIGHT_HOLD_END:
        return hour >= NIGHT_HOLD_START or hour < NIGHT_HOLD_END
    return NIGHT_HOLD_START <= hour < NIGHT_HOLD_END


def seconds_until_morning() -> int:
    """Calculate seconds until the morning window opens."""
    now = datetime.now()
    if now.hour >= NIGHT_HOLD_END:
        morning = now.replace(
            day=now.day + 1, hour=NIGHT_HOLD_END, minute=0, second=0, microsecond=0
        )
    else:
        morning = now.replace(
            hour=NIGHT_HOLD_END, minute=0, second=0, microsecond=0
        )
    return int((morning - now).total_seconds())
