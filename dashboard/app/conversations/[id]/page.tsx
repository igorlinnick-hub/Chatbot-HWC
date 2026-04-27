import { getConversation } from "@/lib/data";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CalendarCheck } from "lucide-react";
import { formatDate } from "@/lib/utils";
import ConversationActions from "@/components/conversation-actions";
import HandoffBanner from "@/components/handoff-banner";

export const dynamic = "force-dynamic";

export default async function ConvoDetail({ params }: { params: { id: string } }) {
  const c = await getConversation(params.id);
  if (!c) notFound();

  const { handoff, booking_link_sent_at, name, timezone, pain_point, duration, ...rest } =
    c.metadata ?? {};
  const KNOWN = { name, timezone, pain_point, duration };
  const knownEntries = Object.entries(KNOWN).filter(([, v]) => v != null && v !== "");
  const extraEntries = Object.entries(rest).filter(([, v]) => v != null && v !== "");

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <Link
        href="/conversations"
        className="inline-flex items-center gap-2 text-sm text-white/50 hover:text-white/80"
      >
        <ArrowLeft className="w-4 h-4" /> Back to conversations
      </Link>

      {handoff && <HandoffBanner conversationId={c.id} handoff={handoff} />}

      <header className="card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className={`badge ${statusClass(c.status)}`}>{c.status}</div>
              <span className="text-xs text-white/50 uppercase tracking-wider">
                {c.platform}
              </span>
              {booking_link_sent_at && (
                <span className="badge bg-violet-500/15 text-violet-200 border border-violet-400/30">
                  <CalendarCheck className="w-3 h-3" /> Link sent {formatDate(booking_link_sent_at)}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-semibold text-white">{c.user_id}</h1>
            <div className="text-white/50 text-sm mt-2">
              Script step{" "}
              <span className="text-violet-300 font-medium">{c.step} / 9</span> · Started{" "}
              {formatDate(c.created_at)} · Last activity {formatDate(c.last_message_at)}
            </div>
          </div>
          <ConversationActions id={c.id} status={c.status} />
        </div>
        {knownEntries.length > 0 && (
          <div className="mt-5 pt-5 border-t border-white/5 grid gap-3 sm:grid-cols-2">
            {knownEntries.map(([k, v]) => (
              <div key={k}>
                <div className="text-[10px] uppercase tracking-wider text-white/40">
                  {k.replace(/_/g, " ")}
                </div>
                <div className="text-sm text-white/85 mt-0.5">{String(v)}</div>
              </div>
            ))}
          </div>
        )}
        {extraEntries.length > 0 && (
          <details className="mt-5 pt-5 border-t border-white/5">
            <summary className="text-xs uppercase tracking-wider text-white/40 cursor-pointer hover:text-white/70 select-none">
              Raw metadata ({extraEntries.length})
            </summary>
            <pre className="text-xs text-violet-200/80 bg-white/5 rounded-xl p-4 overflow-auto mt-3">
              {JSON.stringify(Object.fromEntries(extraEntries), null, 2)}
            </pre>
          </details>
        )}
      </header>

      <section className="card p-0 overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5">
          <div className="text-xs uppercase tracking-wider text-white/40">
            Conversation history · {c.history.length}{" "}
            {c.history.length === 1 ? "message" : "messages"}
          </div>
        </div>
        <div className="p-6 space-y-4">
          {c.history.length === 0 && (
            <div className="text-white/40 text-center py-8">No messages yet.</div>
          )}
          {c.history.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-start" : "justify-end"}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-white/5 border border-white/10 text-white/90"
                    : "bg-gradient-to-br from-violet-500/30 to-violet-700/20 border border-violet-400/30 text-white"
                }`}
              >
                <div className="text-[10px] uppercase tracking-wider opacity-60 mb-1">
                  {m.role === "user" ? "User" : "Leilani"}
                </div>
                {m.content}
              </div>
            </div>
          ))}
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
