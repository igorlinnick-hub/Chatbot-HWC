import hashlib
import hmac
import httpx
from config import INSTAGRAM_PAGE_ACCESS_TOKEN, INSTAGRAM_APP_SECRET

GRAPH_API_URL = "https://graph.facebook.com/v18.0/me/messages"


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify that the webhook payload came from Meta."""
    expected = hmac.new(
        INSTAGRAM_APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def send_typing_indicator(recipient_id: str):
    """Send typing indicator to make it look like Antonia is typing."""
    async with httpx.AsyncClient() as client:
        await client.post(
            GRAPH_API_URL,
            params={"access_token": INSTAGRAM_PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "sender_action": "typing_on",
            },
        )


async def send_message(recipient_id: str, text: str):
    """Send a text message via Instagram DM."""
    async with httpx.AsyncClient() as client:
        await client.post(
            GRAPH_API_URL,
            params={"access_token": INSTAGRAM_PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text},
            },
        )


async def send_long_message(recipient_id: str, text: str, chunk_delay: float = 1.5):
    """
    Split a long message into chunks and send them sequentially
    with delays to mimic real texting.
    """
    import asyncio

    # Split on double newlines or if message is long, split into ~200 char chunks
    if "\n\n" in text:
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    elif len(text) > 250:
        # Split at sentence boundaries
        sentences = text.replace(". ", ".\n").split("\n")
        chunks = []
        current = ""
        for s in sentences:
            if len(current) + len(s) > 250 and current:
                chunks.append(current.strip())
                current = s
            else:
                current = f"{current} {s}" if current else s
        if current.strip():
            chunks.append(current.strip())
    else:
        chunks = [text]

    for i, chunk in enumerate(chunks):
        if i > 0:
            await send_typing_indicator(recipient_id)
            await asyncio.sleep(chunk_delay)
        await send_message(recipient_id, chunk)
