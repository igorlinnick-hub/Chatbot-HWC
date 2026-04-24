from prompts.system_prompt import SYSTEM_PROMPT
from prompts.steps import CONVERSATION_STEPS


# ─────────────────────────────────────────────
# Step instruction text for each step
# ─────────────────────────────────────────────

STEP_INSTRUCTIONS = {
    1: """STEP 1 - OPENER (send_first)
You already sent the opening message. Now the user has replied.
Mirror what they said (1-3 sentences).
Then ask this question (use these words, but ONLY if you haven't asked it before):
"I'm wondering, where in your life do you find your anxiety showing up for you the most?"
If you already asked this in a previous message, DO NOT ask it again. Move the conversation forward naturally.
""",
    2: """STEP 2 - WHERE ANXIETY SHOWS UP
Mirror what they just said (1-3 sentences).
Then ask this question (use these words, but ONLY if you haven't asked it before):
"I'm curious, if you were somehow able to stop the anxiety what would that do for you?"
If you already asked this in a previous message, DO NOT ask it again. Move forward.
""",
    3: """STEP 3 - WHAT STOPPING ANXIETY WOULD DO
Mirror what they said (1-3 sentences).
Then ask this question (use these words, but ONLY if you haven't asked it before):
"And what do you think is preventing you from being able to feel better in general already besides the anxiety?"
If you already asked this in a previous message, DO NOT ask it again. Move forward.
""",
    4: """STEP 4 - WHAT'S PREVENTING THEM
Mirror what they said (1-3 sentences).
Then ask this question (use these words, but ONLY if you haven't asked it before):
"I'm wondering, how important is it for you to make a change now"
If you already asked this in a previous message, DO NOT ask it again. Move forward.
""",
    5: """STEP 5 - IMPORTANCE OF CHANGE
Mirror what they said (1-3 sentences).
Then ask this question (use these words, but ONLY if you haven't asked it before):
"Could I make a suggestion?"
If you already asked this in a previous message, DO NOT ask it again. Move forward.
""",
    6: """STEP 6 - PERMISSION TO SUGGEST
They said yes to "Could I make a suggestion?"
Do NOT mirror. Send this message:
"I know you've mentioned you've been trying to solve this for {duration}, so what we could do is let you set up a free session directly with me to better understand what you've been going through so far, where you want to be and how I could possibly help you overcome {pain_point}."

Then send as a SEPARATE message (after a blank line):
"Would that be helpful for you?"
""",
    7: """STEP 7 - OFFER ACCEPTED
They said yes to the free session offer.
Do NOT mirror. Send these messages as separate messages (separated by blank lines):
"Alright, happy to help."

"Do you have 2 mins to pick a time that's convenient for you to chat, if I send you my calendar? To make it easier for you."
""",
    8: """STEP 8 - READY FOR CALENDAR
They said yes to receiving the calendar.
Do NOT mirror. Send these messages as separate messages (separated by blank lines):
"Great, here's my calendar:"

"https://calendly.com/bloominghypnosis/15min"

"And let me know once you're done so that I can check everything went through properly for you... sometimes calendars act weird"
""",
    9: """STEP 9 - FINAL / POST-BOOKING
They've booked or confirmed. Respond warmly and naturally.
This is the end of the script. Just be human. Keep it short.
""",
}


def build_prompt_for_step(
    step: int,
    corrections: list,
    examples: list,
    metadata: dict | None = None,
) -> str:
    """
    Build the complete system prompt for a given step.
    Injects step instructions, training examples, and corrections.
    """
    prompt = SYSTEM_PROMPT

    # Get step instruction text
    instruction = STEP_INSTRUCTIONS.get(step, STEP_INSTRUCTIONS[1])

    # Fill in metadata variables (duration, pain_point) if present
    if metadata:
        duration = metadata.get("duration") or "a while"
        pain_point = metadata.get("pain_point") or "your anxiety"
        instruction = instruction.replace("{duration}", duration)
        instruction = instruction.replace("{pain_point}", pain_point)

    prompt += f"\n\n---\nCURRENT STEP: {step}\n"
    prompt += f"INSTRUCTION FOR THIS STEP:\n{instruction}\n"

    # Inject training examples if any exist
    if examples:
        prompt += "\n\nEXAMPLES OF IDEAL RESPONSES FROM ANTONIA:\n"
        for ex in examples[-15:]:
            prompt += f"\nUser said: {ex['user_message']}\nAntonia responded: {ex['ideal_response']}\n"

    # Inject recent corrections - these take highest priority
    if corrections:
        prompt += "\n\nRECENT CORRECTIONS - pay close attention to these, they override everything else:\n"
        for c in corrections[-10:]:
            prompt += (
                f"\nContext: {c['context']}\n"
                f"Wrong response: {c['original_response']}\n"
                f"Correct response: {c['corrected_response']}\n"
            )

    return prompt
