from datetime import datetime, timedelta
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_conversation(platform: str, user_id: str) -> dict | None:
    """Fetch an active conversation for a user."""
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("platform", platform)
        .eq("user_id", user_id)
        .in_("status", ["active", "handed_off"])
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_conversation_any_status(platform: str, user_id: str) -> dict | None:
    """Fetch the most recent conversation for a user regardless of status."""
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("platform", platform)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def create_conversation(platform: str, user_id: str) -> dict:
    """Create a new conversation record."""
    result = (
        supabase.table("conversations")
        .insert({
            "platform": platform,
            "user_id": user_id,
            "step": 1,
            "history": [],
            "status": "active",
            "metadata": {},
        })
        .execute()
    )
    return result.data[0]


async def update_conversation(
    platform: str,
    user_id: str,
    step: int,
    history: list,
    metadata: dict,
    status: str,
) -> dict:
    """Update conversation by platform + user_id."""
    result = (
        supabase.table("conversations")
        .update({
            "step": step,
            "history": history,
            "metadata": metadata,
            "status": status,
            "last_message_at": "now()",
        })
        .eq("platform", platform)
        .eq("user_id", user_id)
        .in_("status", ["active", "handed_off"])
        .execute()
    )
    return result.data[0] if result.data else {}


async def save_correction(original: str, corrected: str, context: str) -> dict:
    """Save a correction from Antonia."""
    result = (
        supabase.table("corrections")
        .insert({
            "original_response": original,
            "corrected_response": corrected,
            "context": context,
        })
        .execute()
    )
    return result.data[0]


async def save_training_example(user_message: str, ideal_response: str, notes: str = "") -> dict:
    """Save a training example from Antonia."""
    result = (
        supabase.table("training_examples")
        .insert({
            "user_message": user_message,
            "ideal_response": ideal_response,
            "notes": notes,
        })
        .execute()
    )
    return result.data[0]


async def get_training_examples(limit: int = 15) -> list:
    """Fetch recent training examples for prompt injection."""
    result = (
        supabase.table("training_examples")
        .select("user_message, ideal_response")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


async def get_corrections(limit: int = 10) -> list:
    """Fetch recent corrections for prompt injection."""
    result = (
        supabase.table("corrections")
        .select("context, original_response, corrected_response")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


async def get_active_conversations() -> list:
    """Fetch all active conversations."""
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("status", "active")
        .order("last_message_at", desc=True)
        .execute()
    )
    return result.data


async def set_conversation_status(platform: str, user_id: str, status: str) -> bool:
    """Set conversation status (for handoff/resume)."""
    result = (
        supabase.table("conversations")
        .update({"status": status})
        .eq("platform", platform)
        .eq("user_id", user_id)
        .in_("status", ["active", "handed_off"])
        .execute()
    )
    return bool(result.data)


async def mark_dead_conversations(inactive_days: int = 7) -> int:
    """
    Mark active conversations with no activity for X days as dead.
    Returns count of rows updated.
    """
    cutoff = datetime.utcnow() - timedelta(days=inactive_days)

    result = (
        supabase.table("conversations")
        .update({"status": "dead"})
        .eq("status", "active")
        .lt("last_message_at", cutoff.isoformat())
        .execute()
    )

    return len(result.data) if result.data else 0


# ─── Bot Settings (on/off toggle) ────────────────────────────────────


async def get_bot_enabled() -> bool:
    """Check if the Instagram bot is enabled. Defaults to True if no row exists."""
    result = (
        supabase.table("bot_settings")
        .select("value")
        .eq("key", "instagram_enabled")
        .limit(1)
        .execute()
    )
    if not result.data:
        return True
    return result.data[0]["value"] == "true"


async def set_bot_enabled(enabled: bool) -> None:
    """Toggle the Instagram bot on/off."""
    value = "true" if enabled else "false"
    # Try update first
    result = (
        supabase.table("bot_settings")
        .update({"value": value})
        .eq("key", "instagram_enabled")
        .execute()
    )
    if not result.data:
        # Row doesn't exist, insert it
        supabase.table("bot_settings").insert({
            "key": "instagram_enabled",
            "value": value,
        }).execute()


# ─── Outbound message log (ManyChat buffer) ──────────────────────────


async def log_outbound_message(platform: str, user_id: str) -> None:
    """Log that we sent a message to a user."""
    supabase.table("outbound_log").insert({
        "platform": platform,
        "user_id": user_id,
    }).execute()


async def has_recent_outbound(platform: str, user_id: str, seconds: int = 60) -> bool:
    """Check if any message was sent to this user in the last N seconds."""
    cutoff = (datetime.utcnow() - timedelta(seconds=seconds)).isoformat()
    result = (
        supabase.table("outbound_log")
        .select("id")
        .eq("platform", platform)
        .eq("user_id", user_id)
        .gte("created_at", cutoff)
        .limit(1)
        .execute()
    )
    return bool(result.data)
