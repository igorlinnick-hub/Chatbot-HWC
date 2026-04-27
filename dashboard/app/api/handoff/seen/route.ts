import { NextResponse } from "next/server";
import { markHandoffSeen } from "@/lib/data";

export async function POST(req: Request) {
  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "missing id" }, { status: 400 });
  await markHandoffSeen(id);
  return NextResponse.json({ ok: true });
}
