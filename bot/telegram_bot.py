import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import TELEGRAM_BOT_TOKEN, ANTONIA_TELEGRAM_CHAT_ID
from bot.conversation import generate_response
from bot.handoff import resume_conversation
from prompts.steps import CONVERSATION_STEPS
from db.supabase_client import (
    save_correction,
    save_training_example,
    get_active_conversations,
    set_conversation_status,
    get_conversation,
    create_conversation,
    get_bot_enabled,
    set_bot_enabled,
    update_conversation,
)


logger = logging.getLogger(__name__)


def is_antonia(update: Update) -> bool:
    """Check if the message is from Antonia."""
    return str(update.effective_chat.id) == ANTONIA_TELEGRAM_CHAT_ID


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a practice conversation session."""
    if not is_antonia(update):
        return

    practice_user_id = f"practice_{update.effective_chat.id}"
    platform = "telegram"

    # Reset any existing practice conversation
    convo = await get_conversation(platform, practice_user_id)
    if convo:
        await update_conversation(
            platform=platform,
            user_id=practice_user_id,
            step=1,
            history=[],
            metadata={},
            status="active",
        )

    context.user_data["practice_mode"] = True
    context.user_data["opener_sent"] = False
    await update.message.reply_text(
        "Practice mode started. Send /endchat to stop.\n"
        "─────────────────────"
    )

    # Send the hardcoded step 1 opener — no Claude call
    opener = CONVERSATION_STEPS[1]["message"]

    # Ensure conversation exists in DB with opener in history
    if not convo:
        await create_conversation(platform, practice_user_id)
    await update_conversation(
        platform=platform,
        user_id=practice_user_id,
        step=1,
        history=[{"role": "assistant", "content": opener}],
        metadata={},
        status="active",
    )

    await update.message.reply_text(opener)
    context.user_data["opener_sent"] = True


async def cmd_endchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End practice session."""
    if not is_antonia(update):
        return

    context.user_data["practice_mode"] = False
    await update.message.reply_text("Practice session ended.")


async def cmd_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Correct the last bot response. Usage: /correct <corrected response>"""
    logger.info(f"/correct command received from chat {update.effective_chat.id}")

    if not is_antonia(update):
        logger.info(f"/correct rejected: not Antonia (chat id: {update.effective_chat.id})")
        return

    corrected = update.message.text.replace("/correct ", "", 1).strip()
    if not corrected:
        await update.message.reply_text("Usage: /correct <what it should have said>")
        return

    last = context.user_data.get("last_bot_response", {})
    logger.info(f"/correct last_bot_response: {last}")
    if not last:
        await update.message.reply_text("No recent response to correct.")
        return

    try:
        await save_correction(
            original=last.get("response", ""),
            corrected=corrected,
            context=last.get("user_message", ""),
        )
        await update.message.reply_text(
            "Correction saved. Active now, next response will use it."
        )
    except Exception as e:
        logger.error(f"/correct error: {e}", exc_info=True)
        await update.message.reply_text(f"Error saving correction: {e}")


async def cmd_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a training example. Usage: /teach user: <msg> | response: <msg>"""
    if not is_antonia(update):
        return

    text = update.message.text.replace("/teach ", "", 1).strip()
    if "|" not in text:
        await update.message.reply_text(
            "Usage: /teach user: <their message> | response: <ideal response>"
        )
        return

    parts = text.split("|", 1)
    user_msg = parts[0].replace("user:", "").strip()
    ideal = parts[1].replace("response:", "").strip()

    await save_training_example(user_msg, ideal)
    await update.message.reply_text("Training example saved.")


async def cmd_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Turn Instagram bot ON."""
    if not is_antonia(update):
        return
    await set_bot_enabled(True)
    await update.message.reply_text("Instagram bot is ON. Responding to DMs.")


async def cmd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Turn Instagram bot OFF."""
    if not is_antonia(update):
        return
    await set_bot_enabled(False)
    await update.message.reply_text("Instagram bot is OFF. DMs will be received but not answered.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active conversations count and bot status."""
    if not is_antonia(update):
        return

    convos = await get_active_conversations()
    enabled = await get_bot_enabled()
    status = "ON" if enabled else "OFF"
    await update.message.reply_text(
        f"Bot: {status}\nActive conversations: {len(convos)}"
    )


async def cmd_takeover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Take over a conversation. Usage: /takeover <user_id>"""
    if not is_antonia(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /takeover <user_id>")
        return

    user_id = args[0]
    for platform in ["instagram", "telegram"]:
        success = await set_conversation_status(platform, user_id, "handed_off")
        if success:
            await update.message.reply_text(
                f"Took over conversation with {user_id} on {platform}. "
                "Send /resume <user_id> when done."
            )
            return

    await update.message.reply_text(f"No active conversation found for {user_id}")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resume a conversation. Usage: /resume <user_id>"""
    if not is_antonia(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /resume <user_id>")
        return

    user_id = args[0]
    for platform in ["instagram", "telegram"]:
        success = await resume_conversation(platform, user_id)
        if success:
            await update.message.reply_text(
                f"Resumed bot for {user_id} on {platform}."
            )
            return

    await update.message.reply_text(f"No handed-off conversation found for {user_id}")


async def practice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in practice mode."""
    if not is_antonia(update):
        return
    if not context.user_data.get("practice_mode"):
        return
    if not context.user_data.get("opener_sent"):
        return

    text = update.message.text

    try:
        result = await generate_response(
            "telegram", f"practice_{update.effective_chat.id}", text
        )
    except Exception as e:
        logger.error(f"Practice mode error: {e}", exc_info=True)
        await update.message.reply_text(f"Error: {type(e).__name__}: {e}")
        return

    context.user_data["last_bot_response"] = {
        "response": "\n".join(result["messages"]) if result["messages"] else "",
        "user_message": text,
    }

    if result["messages"]:
        for msg in result["messages"]:
            await update.message.reply_text(msg)
    elif result["handoff"]:
        await update.message.reply_text(
            f"[Handoff triggered: {result['handoff_summary']}]"
        )


async def notify_antonia(app: Application, message: str):
    """Send a notification to Antonia's Telegram."""
    await app.bot.send_message(
        chat_id=ANTONIA_TELEGRAM_CHAT_ID,
        text=message,
    )


def create_telegram_app() -> Application:
    """Build and return the Telegram bot application."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_handler(CommandHandler("endchat", cmd_endchat))
    app.add_handler(CommandHandler("correct", cmd_correct))
    app.add_handler(CommandHandler("teach", cmd_teach))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("on", cmd_on))
    app.add_handler(CommandHandler("off", cmd_off))
    app.add_handler(CommandHandler("takeover", cmd_takeover))
    app.add_handler(CommandHandler("resume", cmd_resume))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, practice_message))

    return app
