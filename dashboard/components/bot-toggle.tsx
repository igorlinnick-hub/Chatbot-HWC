"use client";

import { useState, useTransition } from "react";
import { Power, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function BotToggle({ initial }: { initial: boolean }) {
  const [enabled, setEnabled] = useState(initial);
  const [pending, startTransition] = useTransition();

  async function toggle() {
    const next = !enabled;
    setEnabled(next);
    startTransition(async () => {
      try {
        await fetch("/api/toggle", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ enabled: next }),
        });
      } catch {
        // revert on error
        setEnabled(!next);
      }
    });
  }

  return (
    <div className="card card-hover">
      <div className="flex items-start justify-between gap-6">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-white/50 mb-2">
            Instagram Bot
          </div>
          <div className="text-3xl font-semibold">
            {enabled ? (
              <span className="bg-gradient-to-r from-emerald-300 to-emerald-500 bg-clip-text text-transparent">
                Online
              </span>
            ) : (
              <span className="text-white/40">Offline</span>
            )}
          </div>
          <p className="text-sm text-white/50 mt-2 max-w-sm">
            {enabled
              ? "Bot is responding to DMs via Instagram/ManyChat."
              : "DMs are received but not answered. Safe mode."}
          </p>
        </div>

        <button
          onClick={toggle}
          disabled={pending}
          aria-label="Toggle bot"
          className={cn(
            "relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 group",
            enabled
              ? "bg-gradient-to-br from-violet-400 to-violet-700 shadow-[0_0_40px_-5px_rgba(139,92,246,0.8)]"
              : "bg-white/5 border border-white/10 hover:border-white/20"
          )}
        >
          {pending ? (
            <Loader2 className="w-7 h-7 animate-spin text-white" />
          ) : (
            <Power
              className={cn(
                "w-8 h-8 transition-all",
                enabled ? "text-white" : "text-white/40 group-hover:text-white/70"
              )}
            />
          )}
          {enabled && (
            <span className="absolute inset-0 rounded-full animate-pulse-soft bg-violet-400/20" />
          )}
        </button>
      </div>
    </div>
  );
}
