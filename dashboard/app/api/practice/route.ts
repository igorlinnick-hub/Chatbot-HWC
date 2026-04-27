import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const MOCK_REPLIES = [
  "Aloha, thanks for reaching out. What area of your wellness are you most wanting to work on right now?",
  "That sounds really draining. I'm curious, if you were able to really shift this, what would that change open up for you?",
  "Makes sense given everything you've been carrying. What do you think has been getting in the way of feeling your best already?",
  "I hear you. Could I make a suggestion?",
  "What we could do is set up a free discovery call with one of our coaches. Want me to send the link?",
];

export async function POST(req: Request) {
  const body = await req.json();
  const { message, history = [], session_id } = body;

  // If backend is configured, proxy to it
  try {
    const res = await fetch(`${BACKEND_URL}/practice/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ session_id, message, history }),
      signal: AbortSignal.timeout(30_000),
    });

    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
    // fall through to mock on non-200
  } catch (err) {
    // fall through to mock on network error
  }

  // Mock fallback — cycles through canned replies based on history length
  const idx = Math.min(Math.floor(history.length / 2), MOCK_REPLIES.length - 1);
  await new Promise((r) => setTimeout(r, 800 + Math.random() * 800));
  return NextResponse.json({
    messages: [MOCK_REPLIES[idx]],
    step: Math.min(idx + 2, 9),
    handoff: false,
    mock: true,
  });
}
