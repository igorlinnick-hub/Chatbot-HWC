import { AlertTriangle, HandMetal } from "lucide-react";
import type { HandoffMeta } from "@/lib/types";

export default function HandoffChip({ handoff }: { handoff?: HandoffMeta }) {
  if (!handoff || handoff.seen) return null;
  const urgent = handoff.type === "urgent";
  const Icon = urgent ? AlertTriangle : HandMetal;
  return (
    <span
      className={
        urgent
          ? "badge bg-red-500/15 text-red-200 border border-red-400/40 shadow-[0_0_20px_-6px_rgba(239,68,68,0.7)] animate-pulse-soft"
          : "badge bg-amber-400/15 text-amber-200 border border-amber-300/35"
      }
      title={handoff.summary}
    >
      <Icon className="w-3 h-3" />
      {urgent ? "urgent" : "handoff"}
    </span>
  );
}
