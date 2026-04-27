import { listConversations } from "@/lib/data";
import type { Status } from "@/lib/types";
import Link from "next/link";
import { formatDate, truncate } from "@/lib/utils";
import { Search, Filter } from "lucide-react";
import HandoffChip from "@/components/handoff-chip";

export const dynamic = "force-dynamic";

const STATUSES: (Status | "all")[] = ["all", "active", "booked", "handed_off", "dead"];

export default async function ConversationsPage({
  searchParams,
}: {
  searchParams: { status?: string; q?: string };
}) {
  const status = (searchParams.status ?? "all") as Status | "all";
  const q = searchParams.q ?? "";

  const list = await listConversations({
    status: status === "all" ? undefined : status,
    search: q || undefined,
  });

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl">
      <header>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
          Conversations
        </div>
        <h1 className="text-4xl font-semibold glow-text">All sessions</h1>
        <p className="text-white/50 mt-2">
          {list.length} {list.length === 1 ? "conversation" : "conversations"}
        </p>
      </header>

      <form className="card flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[220px]">
          <label className="label">Search user id</label>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
            <input
              type="search"
              name="q"
              defaultValue={q}
              placeholder="ig_user_…"
              className="input pl-9"
            />
          </div>
        </div>
        <div>
          <label className="label">Status</label>
          <select name="status" defaultValue={status} className="input min-w-[150px]">
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="btn-primary">
          <Filter className="w-4 h-4" /> Apply
        </button>
      </form>

      <div className="card p-0 overflow-hidden divide-y divide-white/5">
        {list.length === 0 && (
          <div className="p-10 text-center text-white/40">
            No conversations match your filters.
          </div>
        )}
        {list.map((c) => {
          const last = c.history[c.history.length - 1];
          return (
            <Link
              key={c.id}
              href={`/conversations/${c.id}`}
              className="flex items-start gap-5 p-5 hover:bg-white/[0.03] transition-colors"
            >
              <div className={`badge ${statusClass(c.status)} shrink-0 mt-1`}>
                {c.status}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center flex-wrap gap-2 text-sm">
                  <span className="text-white/90 font-medium">{c.user_id}</span>
                  <HandoffChip handoff={c.metadata?.handoff} />
                  <span className="text-white/30">·</span>
                  <span className="text-white/50">{c.platform}</span>
                  <span className="text-white/30">·</span>
                  <span className="text-violet-300 font-medium">step {c.step}</span>
                  <span className="text-white/30">·</span>
                  <span className="text-white/50">
                    {c.history.length} {c.history.length === 1 ? "msg" : "msgs"}
                  </span>
                </div>
                {last && (
                  <div className="text-sm text-white/50 mt-2 truncate">
                    <span className="text-white/30">
                      {last.role === "user" ? "👤" : "🤖"}
                    </span>{" "}
                    {truncate(last.content, 120)}
                  </div>
                )}
              </div>
              <div className="text-xs text-white/40 whitespace-nowrap mt-1 text-right">
                <div>{formatDate(c.last_message_at)}</div>
                <div className="text-white/20 mt-1">started {formatDate(c.created_at)}</div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function statusClass(status: string) {
  switch (status) {
    case "active":
      return "badge-active";
    case "booked":
      return "badge-booked";
    case "handed_off":
      return "badge-handed";
    default:
      return "badge-dead";
  }
}
