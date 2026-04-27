import { NextResponse } from "next/server";
import { addTraining, deleteTraining } from "@/lib/data";

export async function POST(req: Request) {
  const body = await req.json();
  await addTraining(body);
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: Request) {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  await deleteTraining(id);
  return NextResponse.json({ ok: true });
}
