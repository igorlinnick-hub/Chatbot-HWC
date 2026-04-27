"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, HandMetal, Check, Loader2 } from "lucide-react";
import type { HandoffMeta } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function HandoffBanner({
  conversationId,
  handoff,
}: {
  conversationId: string;
  handoff: HandoffMeta;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [seen, setSeen] = useState(handoff.seen);

  if (seen) return null;

  const urgent = handoff.type === "urgent";
  const Icon = urgent ? AlertTriangle : HandMetal;

  function markSeen() {
    startTransition(async () => {
      await fetch("/api/handoff/seen", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ id: conversationId }),
      });
      setSeen(true);
      router.refresh();
    });
  }

  return (
    <div
      className={
        urgent
          ? "rounded-2xl border border-red-400/40 bg-gradient-to-br from-red-500/15 via-red-500/5 to-transparent p-5 shadow-[0_0_40px_-10px_rgba(239,68,68,0.5)] animate-fade-in"
          : "rounded-2xl border border-amber-400/35 bg-gradient-to-br from-amber-400/12 via-amber-400/4 to-transparent p-5 animate-fade-in"
      }
    >
      <div className="flex items-start gap-4">
        <div
          className={
            urgent
              ? "w-10 h-10 rounded-xl bg-red-500/25 border border-red-400/40 flex items-center justify-center shrink-0"
              : "w-10 h-10 rounded-xl bg-amber-400/20 border border-amber-300/30 flex items-center justify-center shrink-0"
          }
        >
          <Icon
            className={urgent ? "w-5 h-5 text-red-200" : "w-5 h-5 text-amber-200"}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div
            className={
              urgent
                ? "text-[11px] font-bold uppercase tracking-[0.2em] text-red-200"
                : "text-[11px] font-bold uppercase tracking-[0.2em] text-amber-200"
            }
          >
            {urgent ? "Urgent handoff" : "Handoff"} · {formatDate(handoff.at)}
          </div>
          <div className="text-sm text-white/90 mt-2 leading-relaxed">
            {handoff.summary}
          </div>
          <div className="text-xs text-white/50 mt-2">
            Bot stopped responding. Reply manually or press{" "}
            <span className="text-white/80">Resume bot</span> to hand back.
          </div>
        </div>
        <button
          onClick={markSeen}
          disabled={pending}
          className="btn-ghost shrink-0"
        >
          {pending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Check className="w-4 h-4" />
          )}
          Mark reviewed
        </button>
      </div>
    </div>
  );
}
