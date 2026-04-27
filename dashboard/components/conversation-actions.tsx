"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { HandMetal, Play, Loader2 } from "lucide-react";

export default function ConversationActions({
  id,
  status,
}: {
  id: string;
  status: string;
}) {
  const [pending, startTransition] = useTransition();
  const router = useRouter();
  const [action, setAction] = useState<string | null>(null);

  function doAction(kind: "takeover" | "resume") {
    setAction(kind);
    startTransition(async () => {
      await fetch(`/api/${kind}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ id }),
      });
      setAction(null);
      router.refresh();
    });
  }

  if (status === "handed_off") {
    return (
      <button
        onClick={() => doAction("resume")}
        disabled={pending}
        className="btn-primary"
      >
        {action === "resume" ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Play className="w-4 h-4" />
        )}
        Resume bot
      </button>
    );
  }
  if (status === "active") {
    return (
      <button
        onClick={() => doAction("takeover")}
        disabled={pending}
        className="btn-ghost"
      >
        {action === "takeover" ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <HandMetal className="w-4 h-4" />
        )}
        Take over
      </button>
    );
  }
  return null;
}
