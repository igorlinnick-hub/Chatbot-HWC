import json
import logging
from anthropic import Anthropic
from db.supabase_client import (
    get_conversation,
    create_conversation,
    update_conversation,
    get_corrections,
    get_training_examples,
)
from prompts.prompt_builder import build_prompt_for_step
from prompts.steps import CONVERSATION_STEPS
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────
# EXTRACTION — runs once after step 2 reply
# ─────────────────────────────────────────────

EXTRACT_PROMPT = """
Based on this conversation, extract two things from what the user said:
- duration: how long they've been dealing with this — use their exact words as closely as possible (e.g. "since college", "about 3 years", "a few months on and off")
- pain_point: their specific struggle in their own words — one short phrase (e.g. "freezing up around people I like", "can't speak up at work", "panic attacks in social situations")

Return ONLY valid JSON with no extra text, no markdown, no explanation:
{"duration": "...", "pain_point": "..."}

If the user hasn't mentioned either yet, use null for that field.
"""


async def extract_context(history: list) -> dict:
    """
    Lightweight Claude call to extract duration and pain_point.
    Runs after step 2 is answered. Saves to metadata once.
    """
    try:
        messages = history + [{
            "role": "user",
            "content": EXTRACT_PROMPT,
        }]

        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=100,
            messages=messages,
        )

        raw = response.content[0].text.strip()
        extracted = json.loads(raw)

        return {
            "duration": extracted.get("duration"),
            "pain_point": extracted.get("pain_point"),
        }

    except Exception as e:
        logger.error(f"Context extraction failed: {e}")
        return {"duration": None, "pain_point": None}


# ─────────────────────────────────────────────
# STEP ADVANCEMENT LOGIC
# ─────────────────────────────────────────────

def should_advance_step(current_step: int, user_message: str) -> bool:
    """
    Determines whether the user's reply moves us to the next step.
    Steps 6, 7, 8 require explicit yes before advancing.
    All other steps advance on any substantive reply.
    """
    step_config = CONVERSATION_STEPS.get(current_step, {})
    requires_yes = step_config.get("wait_for_yes", False)

    if requires_yes:
        affirmatives = [
            "yes", "yeah", "yep", "sure", "ok", "okay",
            "absolutely", "definitely", "please", "go ahead",
            "sounds good", "why not", "let's do it", "let's go",
        ]
        return any(word in user_message.lower() for word in affirmatives)

    # Any reply longer than 2 characters advances non-gated steps
    return len(user_message.strip()) > 2


def is_final_step(step: int) -> bool:
    return CONVERSATION_STEPS.get(step, {}).get("is_final", False)


# ─────────────────────────────────────────────
# MAIN GENERATE FUNCTION
# ─────────────────────────────────────────────

async def generate_response(
    platform: str,
    user_id: str,
    user_message: str,
) -> dict:
    """
    Main entry point called by webhook handlers.

    Returns:
    {
        "messages": ["msg1", "msg2"],
        "step": int,
        "handoff": bool,
        "handoff_type": str | None,
        "handoff_summary": str | None,
    }
    """

    # ── 1. Load or create conversation ──────────────────────────
    convo = await get_conversation(platform, user_id)

    if not convo:
        convo = await create_conversation(platform, user_id)
        logger.info(f"New conversation created: {platform}/{user_id}")

    current_step = convo["step"]
    history = convo["history"] or []
    metadata = convo["metadata"] or {}
    status = convo["status"]

    # ── 2. Guard: don't respond if handed off or booked ─────────
    if status in ("handed_off", "booked"):
        logger.info(f"Conversation {platform}/{user_id} is {status} — skipping")
        return {
            "messages": [],
            "step": current_step,
            "handoff": False,
            "handoff_type": None,
            "handoff_summary": None,
        }

    # ── 3. Add user message to history ──────────────────────────
    history.append({"role": "user", "content": user_message})

    # ── 4. Determine if step advances ───────────────────────────
    advance = should_advance_step(current_step, user_message)
    next_step = min(current_step + 1, 9) if advance else current_step

    # ── 5. Extract context after step 2 reply (once only) ───────
    if current_step == 2 and advance and not metadata.get("duration"):
        logger.info("Running context extraction after step 2")
        extracted = await extract_context(history)
        metadata.update(extracted)
        logger.info(f"Extracted: {extracted}")

    # ── 6. Build prompt for the NEXT step ───────────────────────
    corrections = await get_corrections(limit=10)
    examples = await get_training_examples(limit=15)
    system_prompt = build_prompt_for_step(next_step, corrections, examples, metadata)

    # ── 7. Call Claude ───────────────────────────────────────────
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=history,
        )
        raw_response = response.content[0].text.strip()

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        raise

    # ── 8. Check for handoff signals ────────────────────────────
    handoff = False
    handoff_type = None
    handoff_summary = None

    if "[URGENT_HANDOFF:" in raw_response:
        handoff = True
        handoff_type = "urgent"
        handoff_summary = raw_response.split("[URGENT_HANDOFF:")[1].split("]")[0].strip()
        raw_response = raw_response.split("[URGENT_HANDOFF:")[0].strip()

    elif "[OWNER_HANDOFF:" in raw_response:
        handoff = True
        handoff_type = "owner"
        handoff_summary = raw_response.split("[OWNER_HANDOFF:")[1].split("]")[0].strip()
        raw_response = raw_response.split("[OWNER_HANDOFF:")[0].strip()

    # ── 9. Split messages where the step requires it ─────────────
    step_config = CONVERSATION_STEPS.get(next_step, {})
    outgoing_messages = []

    if step_config.get("split_messages"):
        parts = [p.strip() for p in raw_response.split("\n\n") if p.strip()]
        outgoing_messages = parts
    else:
        outgoing_messages = [raw_response]

    # ── 10. Add assistant response to history ───────────────────
    history.append({"role": "assistant", "content": raw_response})

    # ── 11. Determine new status ─────────────────────────────────
    new_status = status
    if handoff:
        new_status = "handed_off"
    elif is_final_step(next_step) and advance:
        new_status = "booked"

    # ── 12. Save everything back to DB ───────────────────────────
    await update_conversation(
        platform=platform,
        user_id=user_id,
        step=next_step,
        history=history,
        metadata=metadata,
        status=new_status,
    )

    return {
        "messages": outgoing_messages,
        "step": next_step,
        "handoff": handoff,
        "handoff_type": handoff_type,
        "handoff_summary": handoff_summary,
    }


# ─────────────────────────────────────────────
# OPENER — called when a new DM is first received
# ─────────────────────────────────────────────

async def send_opener(platform: str, user_id: str) -> dict:
    """
    Called when someone DMs for the first time.
    Step 1 is send_first=True — Antonia initiates, no user message yet.
    """
    convo = await get_conversation(platform, user_id)
    if convo:
        return {"messages": [], "step": convo["step"]}

    convo = await create_conversation(platform, user_id)

    opener = CONVERSATION_STEPS[1]["message"]

    history = [{"role": "assistant", "content": opener}]

    await update_conversation(
        platform=platform,
        user_id=user_id,
        step=1,
        history=history,
        metadata={},
        status="active",
    )

    return {
        "messages": [opener],
        "step": 1,
        "handoff": False,
        "handoff_type": None,
        "handoff_summary": None,
    }
