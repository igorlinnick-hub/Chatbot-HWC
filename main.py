import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import INSTAGRAM_VERIFY_TOKEN
from bot.conversation import generate_response, send_opener
from bot.instagram import verify_signature, send_typing_indicator, send_message
from bot.delay_engine import calculate_delay, is_night_hours, seconds_until_morning
from bot.handoff import trigger_handoff, trigger_booking_notification
from db.supabase_client import get_conversation, mark_dead_conversations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Antonia Bot")
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    scheduler.start()


# ─── Scheduled Jobs ──────────────────────────────────────────────────


@scheduler.scheduled_job("cron", hour=3, minute=0)
async def cleanup_dead_conversations():
    """Mark conversations as dead if no activity for 7 days."""
    count = await mark_dead_conversations(inactive_days=7)
    logger.info(f"Marked {count} conversations as dead")


# ─── Instagram Webhook ───────────────────────────────────────────────


@app.get("/webhook/instagram")
async def instagram_verify(request: Request):
    """Meta webhook verification (GET challenge)."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == INSTAGRAM_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    """Receive Instagram DM messages."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message_text = event.get("message", {}).get("text")

            if not sender_id or not message_text:
                continue

            await schedule_response(
                platform="instagram",
                user_id=sender_id,
                text=message_text,
            )

    return {"status": "ok"}


# ─── Telegram Webhook ────────────────────────────────────────────────


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Placeholder — Telegram bot uses polling via telegram_bot.py."""
    return {"status": "ok"}


# ─── Response Scheduling ─────────────────────────────────────────────


async def schedule_response(platform: str, user_id: str, text: str):
    """Generate response and schedule it with appropriate delay."""

    # ── Check if this is a brand new user ──
    convo = await get_conversation(platform, user_id)
    if not convo:
        opener_result = await send_opener(platform, user_id)
        if opener_result["messages"]:
            await schedule_send(user_id, opener_result["messages"], delay=5)

    # ── Generate response to their message ──
    result = await generate_response(platform, user_id, text)

    if not result["messages"]:
        # ── Handoff triggered — notify Antonia via Telegram ──
        if result["handoff"]:
            convo = await get_conversation(platform, user_id)
            history = convo["history"] if convo else []
            await trigger_handoff(
                platform=platform,
                user_id=user_id,
                handoff_type=result["handoff_type"],
                summary=result["handoff_summary"],
                history=history,
            )
        return

    # ── Calculate delay ──
    delay = calculate_delay(len(text), result["step"])
    if is_night_hours():
        delay = seconds_until_morning()

    await schedule_send(user_id, result["messages"], delay)

    # ── Booking notification when we hit the final step ──
    if result["step"] == 9:
        convo = await get_conversation(platform, user_id)
        metadata = convo["metadata"] if convo else {}
        await trigger_booking_notification(platform, user_id, metadata)


async def schedule_send(user_id: str, messages: list, delay: int):
    """Schedule a list of messages to be sent after a delay."""

    async def send_delayed():
        await send_typing_indicator(user_id)
        await asyncio.sleep(3)

        for i, msg in enumerate(messages):
            if i > 0:
                await send_typing_indicator(user_id)
                await asyncio.sleep(1.5)
            await send_message(user_id, msg)

    run_at = datetime.now() + timedelta(seconds=delay)
    scheduler.add_job(send_delayed, "date", run_date=run_at, misfire_grace_time=300)


# ─── Health Check ─────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "alive"}
