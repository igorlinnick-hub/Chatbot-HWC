import logging

from db.supabase_client import (
    record_booking,
    record_handoff,
    set_conversation_status,
)

logger = logging.getLogger(__name__)


async def trigger_handoff(
    platform: str,
    user_id: str,
    handoff_type: str,
    summary: str,
    history: list,
) -> None:
    """
    Called when Claude returns a handoff signal.
    Marks the conversation as handed_off and stamps the handoff type and
    summary onto metadata. The Vercel dashboard watches `handed_off` rows
    and surfaces the handoff banner there — no push notification.
    """
    await record_handoff(platform, user_id, handoff_type, summary)
    label = "URGENT" if handoff_type == "urgent" else "NORMAL"
    logger.info(
        "Handoff [%s] %s/%s — %s (history=%d msgs)",
        label,
        platform,
        user_id,
        summary,
        len(history),
    )


async def trigger_booking_notification(
    platform: str,
    user_id: str,
    metadata: dict,
) -> None:
    """
    Called when step 9 completes and the booking link has been sent.
    Stamps the booking-sent timestamp on conversation metadata; the
    dashboard renders this on the conversation detail page.
    """
    await record_booking(platform, user_id)
    logger.info(
        "Booking link sent %s/%s — pain=%r duration=%r",
        platform,
        user_id,
        metadata.get("pain_point"),
        metadata.get("duration"),
    )


async def resume_conversation(platform: str, user_id: str) -> bool:
    """Resume a handed-off conversation back to bot control."""
    return await set_conversation_status(platform, user_id, "active")
