import json
import logging
import re
from difflib import SequenceMatcher
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

MAX_REGENERATIONS = 2  # max times to retry if response fails validation


# ─────────────────────────────────────────────
# RESPONSE VALIDATION — prevents repetition
# ─────────────────────────────────────────────

def extract_bot_phrases(history: list) -> list[str]:
    """Extract all previous bot responses as lowercase strings."""
    return [
        msg["content"].lower().strip()
        for msg in history
        if msg["role"] == "assistant" and msg["content"].strip()
    ]


def extract_questions_asked(history: list) -> list[str]:
    """Extract all questions the bot has asked from history."""
    questions = []
    for msg in history:
        if msg["role"] == "assistant":
            # Find sentences ending with ?
            found = re.findall(r'[^.!?\n]*\?', msg["content"])
            questions.extend([q.strip().lower() for q in found if len(q.strip()) > 10])
    return questions


def find_repeated_phrases(history: list, min_length: int = 4) -> set[str]:
    """Find short phrases the bot has used more than once."""
    from collections import Counter
    phrase_counts = Counter()
    for msg in history:
        if msg["role"] == "assistant":
            # Extract 2-4 word phrases
            words = msg["content"].lower().split()
            for n in range(2, min(5, len(words) + 1)):
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i:i+n])
                    if len(phrase) >= min_length:
                        phrase_counts[phrase] += 1
    return {p for p, c in phrase_counts.items() if c >= 2}


def is_similar_to_previous(response: str, history: list, threshold: float = 0.6) -> bool:
    """Check if the response is too similar to any previous bot response."""
    response_lower = response.lower().strip()
    for msg in history:
        if msg["role"] == "assistant":
            prev = msg["content"].lower().strip()
            ratio = SequenceMatcher(None, response_lower, prev).ratio()
            if ratio > threshold:
                logger.warning(f"Response too similar to previous (ratio={ratio:.2f})")
                return True
    return False


def contains_repeated_question(response: str, questions_asked: list[str]) -> bool:
    """Check if the response contains a question that was already asked."""
    response_questions = re.findall(r'[^.!?\n]*\?', response)
    for new_q in response_questions:
        new_q_lower = new_q.strip().lower()
        if len(new_q_lower) < 10:
            continue
        for old_q in questions_asked:
            ratio = SequenceMatcher(None, new_q_lower, old_q).ratio()
            if ratio > 0.7:
                logger.warning(f"Repeated question detected: '{new_q.strip()[:60]}' similar to '{old_q[:60]}'")
                return True
    return False


def validate_response(response: str, history: list) -> tuple[bool, str]:
    """
    Validate bot response against history.
    Returns (is_valid, reason).
    """
    questions_asked = extract_questions_asked(history)

    if contains_repeated_question(response, questions_asked):
        return False, "contains_repeated_question"

    if is_similar_to_previous(response, history, threshold=0.6):
        return False, "too_similar_to_previous"

    return True, "ok"

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
            model="claude-sonnet-4-6",
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

AFFIRMATIVES = [
    "yes", "yeah", "yep", "sure", "ok", "okay",
    "absolutely", "definitely", "please", "go ahead",
    "sounds good", "why not", "let's do it", "let's go",
    "of course", "for sure", "i'd love", "i would love",
    "that would be", "that sounds", "i'm down", "down",
]

NEGATIVES = [
    "no", "nah", "nope", "not really", "i don't think so",
    "not right now", "not sure", "maybe later", "i'm good",
    "not interested", "no thanks", "no thank you", "pass",
    "i'll pass", "not yet", "i can't", "don't want",
]


def is_negative(message: str) -> bool:
    """Check if user message is a negative/refusal response."""
    lower = message.lower().strip()
    return any(neg in lower for neg in NEGATIVES)


def step_question_already_asked(step: int, history: list, metadata: dict | None = None) -> bool:
    """
    Check if the current step's scripted question has already been asked
    by looking at the conversation history.
    """
    step_config = CONVERSATION_STEPS.get(step, {})
    question = step_config.get("message", "")
    if not question:
        return False

    # Fill in metadata placeholders for comparison
    if metadata:
        duration = metadata.get("duration") or "a while"
        pain_point = metadata.get("pain_point") or "your anxiety"
        question = question.replace("{duration}", duration)
        question = question.replace("{pain_point}", pain_point)

    question_lower = question.lower().strip()

    for msg in history:
        if msg["role"] == "assistant":
            content_lower = msg["content"].lower()
            # Check if the scripted question (or most of it) appears in any bot message
            ratio = SequenceMatcher(None, question_lower, content_lower).ratio()
            if ratio > 0.5 or question_lower in content_lower:
                return True
            # Also check partial match — the question might be embedded in a longer message
            if len(question_lower) > 20:
                # Check if a significant chunk of the question appears
                words = question_lower.split()
                key_phrase = " ".join(words[2:min(8, len(words))])  # core of the question
                if key_phrase and key_phrase in content_lower:
                    return True
    return False


def count_bot_responses_on_step(step: int, history: list, metadata: dict | None = None) -> int:
    """
    Count how many times the bot has responded while on this step.
    Uses the step's question text to detect when the step started.
    Falls back to counting recent bot responses.
    """
    step_config = CONVERSATION_STEPS.get(step, {})
    question = step_config.get("message", "")

    if metadata and question:
        duration = metadata.get("duration") or "a while"
        pain_point = metadata.get("pain_point") or "your anxiety"
        question = question.replace("{duration}", duration)
        question = question.replace("{pain_point}", pain_point)

    # Count bot responses from the end of history
    # Every user-bot exchange is one "response on this step"
    count = 0
    for msg in reversed(history):
        if msg["role"] == "assistant":
            count += 1
        # Stop counting if we see a bot message that contains a DIFFERENT step's question
        # (meaning we were on a different step before)
    return count


def should_advance_step(current_step: int, user_message: str, history: list = None, metadata: dict = None) -> bool:
    """
    Determines whether the user's reply moves us to the next step.
    Steps 6, 7, 8 require explicit yes before advancing.
    All other steps advance on any substantive reply.
    Also auto-advances if the current step's question was already asked.
    """
    step_config = CONVERSATION_STEPS.get(current_step, {})
    requires_yes = step_config.get("wait_for_yes", False)

    # Auto-advance if this step's question was already asked in history
    if history and step_question_already_asked(current_step, history, metadata):
        if not requires_yes:
            logger.info(f"Auto-advancing from step {current_step}: question already asked")
            return True

    if requires_yes:
        return any(word in user_message.lower() for word in AFFIRMATIVES)

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
    advance = should_advance_step(current_step, user_message, history, metadata)

    # Calculate next step
    if advance:
        next_step = min(current_step + 1, 9)
        # Skip ahead if the next step's question was already asked
        skip_count = 0
        while (next_step < 9
               and skip_count < 5
               and step_question_already_asked(next_step, history, metadata)
               and not CONVERSATION_STEPS.get(next_step, {}).get("wait_for_yes")):
            logger.info(f"Skipping step {next_step}: question already asked in history")
            next_step += 1
            skip_count += 1
    else:
        next_step = current_step

    # ── 4b. Soft persuasion on "no" at gated steps (6, 7, 8) ──
    step_config = CONVERSATION_STEPS.get(current_step, {})
    soft_persuasion = False
    if step_config.get("wait_for_yes") and not advance and is_negative(user_message):
        refusal_key = f"step_{current_step}_refusals"
        refusal_count = metadata.get(refusal_key, 0) + 1
        metadata[refusal_key] = refusal_count
        logger.info(f"Refusal #{refusal_count} at step {current_step} for {platform}/{user_id}")

        if refusal_count >= 2:
            # Second refusal — handoff to Antonia
            await update_conversation(
                platform=platform, user_id=user_id,
                step=current_step, history=history,
                metadata=metadata, status="handed_off",
            )
            return {
                "messages": [],
                "step": current_step,
                "handoff": True,
                "handoff_type": "owner",
                "handoff_summary": f"User declined twice at step {current_step}. Needs personal follow-up.",
            }

        # First refusal — flag for soft persuasion prompt
        soft_persuasion = True

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

    # If the step's question was already asked, override the instruction
    if step_question_already_asked(next_step, history, metadata):
        step_q = CONVERSATION_STEPS.get(next_step, {}).get("message", "")
        system_prompt += f"""

CRITICAL OVERRIDE — DO NOT REPEAT THIS QUESTION:
The question for this step ("{step_q[:80]}...") has ALREADY been asked in the conversation.
You MUST NOT ask it again in any form — not rephrased, not shortened, not embedded.
Instead: respond naturally to what the user just said. Acknowledge them. Then move the conversation forward by asking something NEW and relevant, or transition to the next topic.
If the user seems confused or off-topic, gently re-engage without repeating past questions.
"""

    # Inject blacklist of already-used phrases and questions
    questions_asked = extract_questions_asked(history)
    repeated_phrases = find_repeated_phrases(history)

    if questions_asked:
        system_prompt += "\n\nQUESTIONS YOU ALREADY ASKED (do NOT ask any of these again, not even rephrased):\n"
        for q in questions_asked:
            system_prompt += f'- "{q}"\n'

    if repeated_phrases:
        top_repeated = sorted(repeated_phrases, key=len, reverse=True)[:15]
        system_prompt += "\n\nPHRASES YOU ALREADY OVERUSED (do NOT use any of these again):\n"
        for p in top_repeated:
            system_prompt += f'- "{p}"\n'

    # Inject soft persuasion override if user said "no" at a gated step
    if soft_persuasion:
        system_prompt += """

IMPORTANT — SOFT RE-ENGAGEMENT:
The user just said no or hesitated. Do NOT repeat the same question. Do NOT pressure them.
Instead, acknowledge their hesitation warmly, then gently reframe the value. Keep it short and natural.
Examples of good responses:
- "Totally understand, no pressure at all. I just thought it could help since you mentioned [their specific struggle]. But totally up to you."
- "No worries at all. I just thought since you've been dealing with this for [duration], it might be worth a quick chat. But I get it."
- "That's completely fine. If anything changes, I'm here."
Stay warm. Stay casual. One short message only. Do NOT re-ask the question.
"""

    # ── 7. Call Claude with validation loop ────────────────────
    raw_response = None
    for attempt in range(MAX_REGENERATIONS + 1):
        try:
            regen_messages = list(history)
            if attempt > 0:
                # On retry, add instruction to avoid the specific problem
                regen_messages = regen_messages + [{
                    "role": "user",
                    "content": f"[System: your previous response was rejected because it {validation_reason}. Write a completely different response. Do NOT repeat any question or phrase from the conversation history.]",
                }]

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=system_prompt,
                messages=regen_messages,
            )
            raw_response = response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

        # Validate response against history
        is_valid, validation_reason = validate_response(raw_response, history)
        if is_valid:
            break
        logger.warning(f"Response validation failed (attempt {attempt + 1}): {validation_reason}")

    if raw_response is None:
        logger.error("No response generated after all attempts")
        raise RuntimeError("Failed to generate valid response")

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
