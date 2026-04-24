import logging
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, ANTONIA_TELEGRAM_CHAT_ID
from db.supabase_client import set_conversation_status

logger = logging.getLogger(__name__)
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def trigger_handoff(
    platform: str,
    user_id: str,
    handoff_type: str,
    summary: str,
    history: list,
) -> None:
    """
    Called when Claude returns a handoff signal.
    1. Marks conversation as handed_off in DB
    2. Sends Antonia a Telegram notification with full context
    """
    await set_conversation_status(platform, user_id, "handed_off")

    emoji = "\U0001f6a8" if handoff_type == "urgent" else "\U0001f44b"
    label = "URGENT — needs immediate attention" if handoff_type == "urgent" else "Ready for you to take over"

    # Last 4 messages for context preview
    recent = history[-4:] if len(history) >= 4 else history
    preview = ""
    for msg in recent:
        role = "Client" if msg["role"] == "user" else "Bot"
        content = msg["content"][:120]
        ellipsis = "..." if len(msg["content"]) > 120 else ""
        preview += f"\n{role}: {content}{ellipsis}"

    notification = (
        f"{emoji} *Handoff — {label}*\n\n"
        f"*Platform:* {platform.capitalize()}\n"
        f"*User ID:* `{user_id}`\n\n"
        f"*Summary:* {summary}\n\n"
        f"*Recent messages:*"
        f"```{preview}```\n\n"
        f"Use `/takeover {user_id}` to respond manually.\n"
        f"Use `/resume {user_id}` to hand back to the bot."
    )

    try:
        await telegram_bot.send_message(
            chat_id=ANTONIA_TELEGRAM_CHAT_ID,
            text=notification,
            parse_mode="Markdown",
        )
        logger.info(f"Handoff notification sent for {platform}/{user_id}")
    except Exception as e:
        logger.error(f"Failed to send Telegram handoff notification: {e}")


async def trigger_booking_notification(
    platform: str,
    user_id: str,
    metadata: dict,
) -> None:
    """
    Called when step 9 completes. Calendly link was sent.
    Notifies Antonia so she knows to expect a booking.
    """
    from datetime import datetime, timezone

    pain_point = metadata.get("pain_point", "not captured")
    duration = metadata.get("duration", "not captured")
    sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    notification = (
        f"\u2705 *Booking link sent*\n\n"
        f"*Platform:* {platform.capitalize()}\n"
        f"*Instagram ID:* `{user_id}`\n"
        f"*Time:* {sent_at}\n\n"
        f"*Their struggle:* {pain_point}\n"
        f"*How long:* {duration}\n\n"
        f"_Calendly link was sent. Watch for the booking confirmation._"
    )

    try:
        await telegram_bot.send_message(
            chat_id=ANTONIA_TELEGRAM_CHAT_ID,
            text=notification,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to send booking notification: {e}")


async def resume_conversation(platform: str, user_id: str) -> bool:
    """Resume a handed-off conversation back to bot control."""
    return await set_conversation_status(platform, user_id, "active")
