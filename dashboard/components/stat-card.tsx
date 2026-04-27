import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent?: "violet" | "emerald" | "amber" | "rose" | "neutral";
  hint?: string;
}

const ACCENT = {
  violet: "from-violet-500/20 to-violet-500/0 text-violet-200 border-violet-400/20",
  emerald: "from-emerald-500/20 to-emerald-500/0 text-emerald-200 border-emerald-400/20",
  amber: "from-amber-500/20 to-amber-500/0 text-amber-200 border-amber-400/20",
  rose: "from-rose-500/20 to-rose-500/0 text-rose-200 border-rose-400/20",
  neutral: "from-white/10 to-white/0 text-white/60 border-white/10",
};

export default function StatCard({
  label,
  value,
  icon: Icon,
  accent = "violet",
  hint,
}: Props) {
  return (
    <div className="card card-hover group">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-white/50">
            {label}
          </div>
          <div className="text-4xl font-semibold text-white mt-2">{value}</div>
          {hint && <div className="text-xs text-white/40 mt-2">{hint}</div>}
        </div>
        <div
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br border",
            ACCENT[accent]
          )}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
