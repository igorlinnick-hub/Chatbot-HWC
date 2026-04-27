import { NextResponse } from "next/server";
import { setBotEnabled } from "@/lib/data";

export async function POST(req: Request) {
  const { enabled } = await req.json().catch(() => ({ enabled: true }));
  await setBotEnabled(Boolean(enabled));
  return NextResponse.json({ ok: true, enabled: Boolean(enabled) });
}
