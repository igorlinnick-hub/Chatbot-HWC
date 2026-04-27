import { NextResponse } from "next/server";
import { setConversationStatus } from "@/lib/data";

export async function POST(req: Request) {
  const { id } = await req.json();
  await setConversationStatus(id, "active");
  return NextResponse.json({ ok: true });
}
