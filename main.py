import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import INSTAGRAM_VERIFY_TOKEN, TELEGRAM_BOT_TOKEN, INSTAGRAM_PAGE_ID
from bot.conversation import generate_response, send_opener
from bot.instagram import verify_signature, send_typing_indicator, send_message
from bot.delay_engine import calculate_delay, calculate_manychat_delay, is_night_hours, seconds_until_morning
from bot.handoff import trigger_handoff, trigger_booking_notification
from bot.telegram_bot import create_telegram_app
from db.supabase_client import (
    get_conversation,
    get_conversation_any_status,
    mark_dead_conversations,
    get_bot_enabled,
    has_recent_outbound,
    log_outbound_message,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Antonia Bot")
scheduler = AsyncIOScheduler()

# ─── Message batching for ManyChat ───────────────────────────────────
# Collects rapid-fire messages per subscriber before processing
_manychat_batches: dict[str, list[str]] = {}
_manychat_locks: dict[str, asyncio.Lock] = {}
_manychat_processing: dict[str, bool] = {}
MANYCHAT_BATCH_WINDOW = 3  # seconds to wait for additional messages

telegram_app = None


@app.on_event("startup")
async def startup():
    global telegram_app
    scheduler.start()

    # Start Telegram bot polling alongside FastAPI
    if TELEGRAM_BOT_TOKEN:
        telegram_app = create_telegram_app()
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram bot polling started")


@app.on_event("shutdown")
async def shutdown():
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("Telegram bot stopped")


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

    # Get the page ID from the webhook entry to filter out page's own messages
    for entry in data.get("entry", []):
        page_id = entry.get("id", "")

        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            recipient_id = event.get("recipient", {}).get("id")
            message_text = event.get("message", {}).get("text")

            if not sender_id or not message_text:
                continue

            # Filter out messages FROM the page/bot itself
            if sender_id == page_id or sender_id == INSTAGRAM_PAGE_ID:
                logger.debug(f"Skipping outbound message from page: {sender_id}")
                continue

            # Also skip echo messages (messages sent by the page)
            if event.get("message", {}).get("is_echo"):
                logger.debug("Skipping echo message")
                continue

            await schedule_response(
                platform="instagram",
                user_id=sender_id,
                text=message_text,
            )

    return {"status": "ok"}


# ─── ManyChat Webhook ────────────────────────────────────────────────


@app.post("/webhook/manychat")
async def manychat_webhook(request: Request):
    """
    Receive messages forwarded by ManyChat.
    Returns synchronous ManyChat v2 response — no delay engine.
    ManyChat handles its own sending timing via Smart Delay.
    """
    # ── Parse request body: JSON, form-encoded, or raw text ──
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            data = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            data = dict(form)
        else:
            # Try JSON first, fall back to form
            body = await request.body()
            try:
                import json
                data = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                data = dict(await request.form()) if body else {}
    except Exception as e:
        logger.error(f"ManyChat request parse error: {e}")
        data = {}

    logger.info(f"ManyChat request received: content-type={content_type}, data={data}")

    subscriber_id = str(data.get("subscriber_id", ""))
    user_message = str(data.get("last_input_text", "")).strip()
    empty_response = {"version": "v2", "content": {"messages": []}}

    if not subscriber_id:
        return empty_response

    # ── Filter ManyChat trigger messages ──
    if not user_message or len(user_message) < 3 or user_message.lower() in MANYCHAT_TRIGGER_WORDS:
        logger.info(f"ManyChat trigger message filtered: '{user_message}' from {subscriber_id}")
        return empty_response

    # ── Check global on/off toggle ──
    if not await get_bot_enabled():
        logger.info(f"Bot is OFF, skipping ManyChat response to {subscriber_id}")
        return empty_response

    # ── Check conversation state (any status) ──
    from datetime import datetime, timedelta, timezone
    convo = await get_conversation_any_status("instagram", subscriber_id)

    # 1. Brand new user → ManyChat already sent the opener, so create conversation
    #    with opener in history and process their reply as response to step 1
    if convo is None:
        logger.info(f"New ManyChat user {subscriber_id}, creating conversation (ManyChat already sent opener)")
        from db.supabase_client import create_conversation, update_conversation
        from prompts.steps import CONVERSATION_STEPS
        opener_text = CONVERSATION_STEPS[1]["message"]
        await create_conversation("instagram", subscriber_id)
        await update_conversation(
            platform="instagram",
            user_id=subscriber_id,
            step=1,
            history=[{"role": "assistant", "content": opener_text}],
            metadata={},
            status="active",
        )
        # Now process their message as a reply to step 1
        result = await generate_response("instagram", subscriber_id, user_message)
        if not result["messages"]:
            return empty_response
        combined = "\n\n".join(result["messages"])
        return {"version": "v2", "content": {"messages": [{"type": "text", "text": combined}]}}

    status = convo.get("status", "active")
    history = convo.get("history", [])
    last_message_at = convo.get("last_message_at", "")

    # 2. Booked or handed off → do NOT respond
    if status in ("booked", "handed_off"):
        logger.info(f"Skipping {subscriber_id}: status is {status}")
        return empty_response

    # 3. Dead conversations or old ones re-engaging → handoff to owner
    try:
        last_msg_time = datetime.fromisoformat(last_message_at.replace("Z", "+00:00"))
        days_since_last = (datetime.now(timezone.utc) - last_msg_time).days
    except (ValueError, AttributeError):
        days_since_last = 0

    if len(history) > 6 and days_since_last > 7:
        logger.info(f"Old conversation re-engaged: {subscriber_id} ({len(history)} msgs, {days_since_last} days ago)")
        await trigger_handoff(
            platform="instagram",
            user_id=subscriber_id,
            handoff_type="normal",
            summary=f"Existing client re-engaged after {days_since_last} day gap. {len(history)} messages in history.",
            history=history,
        )
        return empty_response

    # 4. Active mid-script → batch messages then respond
    # If another request is already processing for this subscriber, add to batch and return empty
    if subscriber_id not in _manychat_locks:
        _manychat_locks[subscriber_id] = asyncio.Lock()

    if _manychat_processing.get(subscriber_id):
        # Another request is already waiting/processing — add message to batch
        _manychat_batches.setdefault(subscriber_id, []).append(user_message)
        logger.info(f"ManyChat: batched message for {subscriber_id} ({len(_manychat_batches[subscriber_id])} in queue)")
        return empty_response

    # First message — mark as processing, wait for batch window, then process all
    _manychat_processing[subscriber_id] = True
    _manychat_batches[subscriber_id] = [user_message]

    step = convo.get("step", 1)
    delay = calculate_manychat_delay(len(user_message), step)

    # Wait: batch window + natural delay (capped so total stays under 10s)
    total_wait = min(MANYCHAT_BATCH_WINDOW + delay, 8.0)
    logger.info(f"ManyChat: waiting {total_wait:.1f}s for {subscriber_id} (batch + delay, step {step})")
    await asyncio.sleep(total_wait)

    # Combine all batched messages into one
    batched_messages = _manychat_batches.pop(subscriber_id, [user_message])
    _manychat_processing[subscriber_id] = False
    combined_input = " ".join(batched_messages)
    logger.info(f"ManyChat: processing {len(batched_messages)} message(s) for {subscriber_id}: '{combined_input[:100]}'")

    result = await generate_response("instagram", subscriber_id, combined_input)

    # ── Handoff ──
    if not result["messages"] and result["handoff"]:
        convo = await get_conversation("instagram", subscriber_id)
        history = convo["history"] if convo else []
        await trigger_handoff(
            platform="instagram",
            user_id=subscriber_id,
            handoff_type=result["handoff_type"],
            summary=result["handoff_summary"],
            history=history,
        )
        return empty_response

    # ── Booking notification ──
    if result["step"] >= 9:
        convo = await get_conversation("instagram", subscriber_id)
        metadata = convo["metadata"] if convo else {}
        await trigger_booking_notification("instagram", subscriber_id, metadata)

    # ── Build ManyChat v2 response — single combined message ──
    combined = "\n\n".join(result["messages"]) if result["messages"] else ""
    if not combined:
        return empty_response
    return {"version": "v2", "content": {"messages": [{"type": "text", "text": combined}]}}


# ─── Telegram Webhook ────────────────────────────────────────────────


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Placeholder - Telegram bot uses polling via telegram_bot.py."""
    return {"status": "ok"}


# ─── Response Scheduling ─────────────────────────────────────────────

MANYCHAT_NEW_CONVO_DELAY = 30  # seconds to wait before responding to new users
MANYCHAT_OPENER_DELAY = 35  # seconds to wait before sending opener to new ManyChat users
MANYCHAT_TRIGGER_WORDS = {"start", "hello", "hi", "hey"}


async def schedule_response(platform: str, user_id: str, text: str):
    """
    Generate response and schedule it with appropriate delay.

    ManyChat flow:
    1. ManyChat sends outbound to new follower (filtered out by webhook, we never see it)
    2. User replies to ManyChat's message (incoming, we pick it up here)
    3. If new conversation: wait 30s so ManyChat can finish its flow, then respond
    4. If existing conversation: respond normally with calculated delay
    """

    # ── Check global on/off toggle ──
    if not await get_bot_enabled():
        logger.info(f"Bot is OFF, skipping response to {user_id}")
        return

    # ── Check if this is a brand new user ──
    convo = await get_conversation(platform, user_id)
    is_new = convo is None

    if is_new:
        # New user: wait 30s to let ManyChat finish its flow
        logger.info(f"New user {user_id}, waiting {MANYCHAT_NEW_CONVO_DELAY}s for ManyChat buffer")
        await asyncio.sleep(MANYCHAT_NEW_CONVO_DELAY)

        opener_result = await send_opener(platform, user_id)
        if opener_result["messages"]:
            await schedule_send(platform, user_id, opener_result["messages"], delay=5)

    # ── Generate response to their message ──
    result = await generate_response(platform, user_id, text)

    if not result["messages"]:
        # ── Handoff triggered - notify Antonia via Telegram ──
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

    await schedule_send(platform, user_id, result["messages"], delay)

    # ── Booking notification when we reach or are on the final step ──
    if result["step"] >= 9:
        convo = await get_conversation(platform, user_id)
        metadata = convo["metadata"] if convo else {}
        await trigger_booking_notification(platform, user_id, metadata)


async def schedule_send(platform: str, user_id: str, messages: list, delay: int):
    """Schedule a list of messages to be sent after a delay."""

    async def send_delayed():
        await send_typing_indicator(user_id)
        await asyncio.sleep(3)

        for i, msg in enumerate(messages):
            if i > 0:
                await send_typing_indicator(user_id)
                await asyncio.sleep(1.5)
            await send_message(user_id, msg)

        # Log that we sent messages
        await log_outbound_message(platform, user_id)

    run_at = datetime.now() + timedelta(seconds=delay)
    scheduler.add_job(send_delayed, "date", run_date=run_at, misfire_grace_time=300)


# ─── Health Check ─────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "alive"}
