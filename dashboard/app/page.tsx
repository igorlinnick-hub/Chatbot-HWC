import {
  Activity,
  CalendarCheck,
  HandMetal,
  Skull,
  PencilLine,
  BookOpen,
  Database,
} from "lucide-react";
import { getBotEnabled, getStats, listConversations, isSupabaseConfigured } from "@/lib/data";
import BotToggle from "@/components/bot-toggle";
import StatCard from "@/components/stat-card";
import HandoffChip from "@/components/handoff-chip";
import Link from "next/link";
import { formatDate, truncate } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [enabled, stats, recent] = await Promise.all([
    getBotEnabled(),
    getStats(),
    listConversations(),
  ]);

  const recentFive = recent.slice(0, 5);

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
            Control Centre
          </div>
          <h1 className="text-4xl md:text-5xl font-semibold glow-text">
            Aloha.
          </h1>
          <p className="text-white/50 mt-2">
            Here's how the clinic's intake bot is doing right now.
          </p>
        </div>
        {!isSupabaseConfigured && (
          <div className="badge bg-amber-500/10 text-amber-200 border border-amber-400/30">
            <Database className="w-3.5 h-3.5" /> Showing mock data — configure Supabase in <code className="mx-1">.env.local</code>
          </div>
        )}
      </header>

      <section className="grid gap-4 lg:grid-cols-2">
        <BotToggle initial={enabled} />
        <div className="card card-hover">
          <div className="text-xs font-medium uppercase tracking-wider text-white/50 mb-2">
            Today's Script
          </div>
          <div className="text-3xl font-semibold text-white">
            9-step qualifier
          </div>
          <p className="text-sm text-white/50 mt-2">
            Mirrors → validates → qualifies → books via Calendly. Natural delays, night-hour hold, correction loop.
          </p>
          <Link href="/about" className="btn-ghost mt-5">
            How it works →
          </Link>
        </div>
      </section>

      <section className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatCard label="Active" value={stats.active} icon={Activity} accent="emerald" />
        <StatCard label="Booked" value={stats.booked} icon={CalendarCheck} accent="violet" />
        <StatCard label="Handed off" value={stats.handed_off} icon={HandMetal} accent="amber" />
        <StatCard label="Dead" value={stats.dead} icon={Skull} accent="neutral" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <StatCard label="Corrections" value={stats.total_corrections} icon={PencilLine} accent="rose" hint="Saved response corrections feeding the prompt" />
        <StatCard label="Training examples" value={stats.total_training} icon={BookOpen} accent="violet" hint="Ideal user→response pairs in rotation" />
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white/90">Recent activity</h2>
          <Link href="/conversations" className="text-sm text-violet-300 hover:text-violet-200">
            View all →
          </Link>
        </div>
        <div className="card divide-y divide-white/5 p-0 overflow-hidden">
          {recentFive.length === 0 && (
            <div className="p-6 text-white/40 text-sm">No conversations yet.</div>
          )}
          {recentFive.map((c) => {
            const last = c.history[c.history.length - 1];
            return (
              <Link
                key={c.id}
                href={`/conversations/${c.id}`}
                className="flex items-start gap-4 p-5 hover:bg-white/[0.03] transition-colors"
              >
                <div className={`badge ${statusClass(c.status)}`}>{c.status}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center flex-wrap gap-2 text-sm">
                    <span className="text-white/90 font-medium">{c.user_id}</span>
                    <HandoffChip handoff={c.metadata?.handoff} />
                    <span className="text-white/30">·</span>
                    <span className="text-white/50">{c.platform}</span>
                    <span className="text-white/30">·</span>
                    <span className="text-violet-300">step {c.step}</span>
                  </div>
                  {last && (
                    <div className="text-sm text-white/50 mt-1 truncate">
                      <span className="text-white/30">{last.role === "user" ? "👤" : "🤖"}</span>{" "}
                      {truncate(last.content, 90)}
                    </div>
                  )}
                </div>
                <div className="text-xs text-white/40 whitespace-nowrap">
                  {formatDate(c.last_message_at)}
                </div>
              </Link>
            );
          })}
        </div>
      </section>
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
