"use client";

import { useRef, useState, useEffect } from "react";
import { Send, Loader2, RefreshCcw } from "lucide-react";
import type { Message } from "@/lib/types";

export default function PracticeChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [sessionId] = useState(() => `practice_${Math.random().toString(36).slice(2, 10)}`);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  function reset() {
    setMessages([]);
    setInput("");
    setError(null);
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || pending) return;

    if (text === "/reset") {
      reset();
      return;
    }

    const userMsg: Message = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setPending(true);
    setError(null);

    try {
      const res = await fetch("/api/practice", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          history: messages,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Request failed");
      } else {
        const replies: string[] = data.messages ?? [];
        setMessages((m) => [
          ...m,
          ...replies.map((r): Message => ({ role: "assistant", content: r })),
        ]);
        if (data.handoff) {
          setMessages((m) => [
            ...m,
            { role: "assistant", content: `[Handoff would trigger: ${data.handoff_summary ?? "urgent"}]` },
          ]);
        }
      }
    } catch (err: any) {
      setError(err.message ?? "Network error");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="card p-0 overflow-hidden flex flex-col h-[65vh] min-h-[500px]">
      <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs uppercase tracking-wider text-white/50">
            Practice session · {sessionId.slice(-8)}
          </span>
        </div>
        <button onClick={reset} className="text-white/40 hover:text-white text-xs flex items-center gap-1.5">
          <RefreshCcw className="w-3.5 h-3.5" /> Reset
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-white/40 py-12">
            Type a message to start practising. Try:{" "}
            <span className="text-violet-300">"hey i have really bad anxiety"</span>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-white/10 border border-white/10 text-white/90"
                  : "bg-gradient-to-br from-violet-500/30 to-violet-700/20 border border-violet-400/30 text-white"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {pending && (
          <div className="flex justify-start">
            <div className="bg-gradient-to-br from-violet-500/20 to-violet-700/10 border border-violet-400/20 rounded-2xl px-4 py-3 flex gap-1">
              <span className="w-1.5 h-1.5 bg-violet-300 rounded-full animate-pulse-soft" />
              <span className="w-1.5 h-1.5 bg-violet-300 rounded-full animate-pulse-soft [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-violet-300 rounded-full animate-pulse-soft [animation-delay:0.4s]" />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="px-5 py-2 text-xs text-red-300 bg-red-500/10 border-t border-red-500/20">
          {error}
        </div>
      )}

      <form onSubmit={send} className="p-4 border-t border-white/5 flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="input"
          disabled={pending}
        />
        <button type="submit" disabled={pending || !input.trim()} className="btn-primary">
          {pending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
}
