import { NextResponse } from "next/server";
import { addCorrection, deleteCorrection } from "@/lib/data";

export async function POST(req: Request) {
  const body = await req.json();
  await addCorrection(body);
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: Request) {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  await deleteCorrection(id);
  return NextResponse.json({ ok: true });
}
