"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, Loader2 } from "lucide-react";

export default function CorrectionForm() {
  const [open, setOpen] = useState(false);
  const [context, setContext] = useState("");
  const [original, setOriginal] = useState("");
  const [corrected, setCorrected] = useState("");
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    startTransition(async () => {
      await fetch("/api/corrections", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          context,
          original_response: original,
          corrected_response: corrected,
        }),
      });
      setContext("");
      setOriginal("");
      setCorrected("");
      setOpen(false);
      router.refresh();
    });
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn-primary">
        <Plus className="w-4 h-4" /> Add correction
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="card space-y-4">
      <div>
        <label className="label">User said</label>
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          rows={2}
          className="input"
          placeholder="What the user wrote…"
          required
        />
      </div>
      <div>
        <label className="label text-red-300/70">Bot originally said</label>
        <textarea
          value={original}
          onChange={(e) => setOriginal(e.target.value)}
          rows={3}
          className="input"
          placeholder="What the bot replied with (the mistake)…"
          required
        />
      </div>
      <div>
        <label className="label text-emerald-300/70">Should have said</label>
        <textarea
          value={corrected}
          onChange={(e) => setCorrected(e.target.value)}
          rows={3}
          className="input"
          placeholder="What the response should have been…"
          required
        />
      </div>
      <div className="flex gap-3">
        <button type="submit" disabled={pending} className="btn-primary">
          {pending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Save correction
        </button>
        <button type="button" onClick={() => setOpen(false)} className="btn-ghost">
          Cancel
        </button>
      </div>
    </form>
  );
}
