import {
  Brain,
  Instagram,
  Database,
  Calendar,
  Webhook,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import CopyButton from "@/components/copy-button";

export const dynamic = "force-dynamic";

interface Integration {
  key: string;
  name: string;
  icon: typeof Brain;
  env: string[];
  description: string;
  configured: boolean;
  color: string;
}

export default function IntegrationsPage() {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const has = (k: string) => Boolean(process.env[k]);

  const integrations: Integration[] = [
    {
      key: "claude",
      name: "Anthropic Claude",
      icon: Brain,
      env: ["ANTHROPIC_API_KEY"],
      description: "Language model behind every response. claude-sonnet-4-6.",
      configured: has("ANTHROPIC_API_KEY"),
      color: "from-orange-400/20 to-pink-500/10 border-orange-400/20",
    },
    {
      key: "instagram",
      name: "Instagram / Meta",
      icon: Instagram,
      env: ["INSTAGRAM_PAGE_ACCESS_TOKEN", "INSTAGRAM_APP_SECRET", "INSTAGRAM_VERIFY_TOKEN", "INSTAGRAM_PAGE_ID"],
      description: "Incoming DMs via Meta webhook + typing indicators + outgoing messages.",
      configured: has("INSTAGRAM_PAGE_ACCESS_TOKEN"),
      color: "from-fuchsia-400/20 to-pink-500/10 border-fuchsia-400/20",
    },
    {
      key: "manychat",
      name: "ManyChat",
      icon: Webhook,
      env: [],
      description:
        "Optional — routes Instagram messages through ManyChat. Configured in ManyChat dashboard, not env.",
      configured: true,
      color: "from-sky-400/20 to-cyan-500/10 border-sky-400/20",
    },
    {
      key: "supabase",
      name: "Supabase",
      icon: Database,
      env: ["NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
      description: "Postgres. Tables: conversations, corrections, training_examples, bot_settings, outbound_log.",
      configured: has("NEXT_PUBLIC_SUPABASE_URL") && has("SUPABASE_SERVICE_ROLE_KEY"),
      color: "from-emerald-400/20 to-green-500/10 border-emerald-400/20",
    },
    {
      key: "booking",
      name: "Booking link",
      icon: Calendar,
      env: ["BOOKING_LINK"],
      description: "Calendly / Cal.com / etc. URL the bot sends at step 9 (free discovery call).",
      configured: has("BOOKING_LINK"),
      color: "from-violet-400/20 to-purple-500/10 border-violet-400/20",
    },
  ];

  const webhooks = [
    { label: "Instagram (Meta)", url: `${backendUrl}/webhook/instagram` },
    { label: "ManyChat", url: `${backendUrl}/webhook/manychat` },
    { label: "Health check", url: `${backendUrl}/health` },
  ];

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl">
      <header>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
          Connections
        </div>
        <h1 className="text-4xl font-semibold glow-text">Integrations</h1>
        <p className="text-white/50 mt-2">
          All external services the bot talks to. Green means credentials are loaded, red
          means missing.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        {integrations.map((i) => {
          const Icon = i.icon;
          return (
            <div key={i.key} className="card card-hover">
              <div className="flex items-start gap-4">
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br border ${i.color} flex items-center justify-center shrink-0`}
                >
                  <Icon className="w-6 h-6 text-white/80" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-white">{i.name}</h3>
                    {i.configured ? (
                      <span className="badge-active">
                        <CheckCircle2 className="w-3 h-3" /> Connected
                      </span>
                    ) : (
                      <span className="badge bg-red-500/10 text-red-300 border border-red-500/25">
                        <XCircle className="w-3 h-3" /> Missing
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-white/60 mt-1.5">{i.description}</p>
                  {i.env.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {i.env.map((e) => (
                        <code
                          key={e}
                          className="text-[11px] px-2 py-0.5 bg-white/5 rounded border border-white/10 text-violet-200/90"
                        >
                          {e}
                        </code>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </section>

      <section>
        <h2 className="text-sm uppercase tracking-wider text-white/40 mb-3">
          Webhook URLs
        </h2>
        <div className="card p-0 overflow-hidden divide-y divide-white/5">
          {webhooks.map((w) => (
            <div
              key={w.url}
              className="flex items-center justify-between gap-4 px-5 py-4"
            >
              <div>
                <div className="text-sm font-medium text-white/90">{w.label}</div>
                <code className="text-xs text-violet-200/80">{w.url}</code>
              </div>
              <CopyButton text={w.url} />
            </div>
          ))}
        </div>
        <p className="text-xs text-white/40 mt-3">
          Set <code className="text-violet-300">BACKEND_URL</code> env var to your
          production backend (e.g. Railway URL) so these display correctly.
        </p>
      </section>
    </div>
  );
}
