"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, Loader2 } from "lucide-react";

export default function TrainingForm() {
  const [open, setOpen] = useState(false);
  const [userMsg, setUserMsg] = useState("");
  const [ideal, setIdeal] = useState("");
  const [notes, setNotes] = useState("");
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    startTransition(async () => {
      await fetch("/api/training", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          user_message: userMsg,
          ideal_response: ideal,
          notes: notes || undefined,
        }),
      });
      setUserMsg("");
      setIdeal("");
      setNotes("");
      setOpen(false);
      router.refresh();
    });
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn-primary">
        <Plus className="w-4 h-4" /> Add training example
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="card space-y-4">
      <div>
        <label className="label">User message</label>
        <textarea
          value={userMsg}
          onChange={(e) => setUserMsg(e.target.value)}
          rows={2}
          className="input"
          placeholder="What a user might say…"
          required
        />
      </div>
      <div>
        <label className="label text-violet-300/70">Ideal response</label>
        <textarea
          value={ideal}
          onChange={(e) => setIdeal(e.target.value)}
          rows={4}
          className="input"
          placeholder="How Leilani should respond…"
          required
        />
      </div>
      <div>
        <label className="label">Notes (optional)</label>
        <input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="input"
          placeholder="Why this response is good…"
        />
      </div>
      <div className="flex gap-3">
        <button type="submit" disabled={pending} className="btn-primary">
          {pending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Save example
        </button>
        <button type="button" onClick={() => setOpen(false)} className="btn-ghost">
          Cancel
        </button>
      </div>
    </form>
  );
}
