import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const MOCK_REPLIES = [
  "Hey love, so glad you reached out. Tell me what's been on your heart lately?",
  "Oh, that sounds really heavy. I hear you. Can I ask — when did you first notice it getting worse?",
  "That makes so much sense given everything you're carrying. Has anything at all helped, even a little?",
  "I love that you're looking into this. Hypnotherapy is incredibly gentle — most people feel the shift in the first session. Want me to send over my calendar?",
  "Here's my link, love: https://calendly.com/bloominghypnosis/15min — grab whatever works for you 💜",
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
