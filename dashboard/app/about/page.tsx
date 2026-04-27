import {
  Sparkles,
  ListOrdered,
  Heart,
  Clock,
  Moon,
  HandMetal,
  Repeat,
  MessageSquare,
  Workflow,
} from "lucide-react";

const STEPS = [
  { n: 1, emotional: "low", text: "Aloha, thanks for the follow. Are you here for the content or exploring how we could support your wellness journey?" },
  { n: 2, emotional: "medium", text: "I'm wondering, what area of your wellness are you most wanting to work on right now?" },
  { n: 3, emotional: "medium", text: "I'm curious, if you were able to really shift this, what would that change open up for you?" },
  { n: 4, emotional: "high", text: "And what do you think has been getting in the way of feeling your best already?" },
  { n: 5, emotional: "high", text: "How important is it for you to make a change now?" },
  { n: 6, emotional: "low", text: "Could I make a suggestion?" },
  { n: 7, emotional: "high", text: "Offer: free discovery call with a coach to understand the goal and explore fit." },
  { n: 8, emotional: "low", text: "Ask if they have 2 mins to pick a calendar slot." },
  { n: 9, emotional: "low", text: "Send the booking link. Follow up: \"let me know when done so I can check it went through.\"" },
];

export default function AboutPage() {
  return (
    <div className="space-y-10 animate-fade-in max-w-4xl">
      <header>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
          The Bot
        </div>
        <h1 className="text-4xl font-semibold glow-text">How Leilani works</h1>
        <p className="text-white/60 mt-3 leading-relaxed">
          Leilani is the Hawaii Wellness Clinic's intake assistant — a
          conversation-first AI on the clinic's Instagram DMs. She mirrors clients
          warmly, follows a deliberate 9-step qualifier, matches the clinic's voice,
          respects natural timing, and hands off cleanly when something needs a human.
          Nothing about her is generic — every response goes through a mirror-first
          filter, is validated against the current script step, and is reshaped using
          saved corrections and training examples.
        </p>
      </header>

      <Section icon={Workflow} title="Architecture at a glance">
        <div className="grid md:grid-cols-2 gap-3 text-sm text-white/70">
          <Bullet>FastAPI webhook server hosting Instagram + ManyChat endpoints</Bullet>
          <Bullet>Claude Sonnet 4.6 with full history passed every call</Bullet>
          <Bullet>Supabase Postgres — conversations, corrections, training_examples, bot_settings, outbound_log</Bullet>
          <Bullet>APScheduler for natural delays + nightly cleanup</Bullet>
          <Bullet>ManyChat v2 sync response (no delay engine, ManyChat handles timing)</Bullet>
          <Bullet>This Next.js dashboard (Vercel) as the only admin surface</Bullet>
        </div>
      </Section>

      <Section icon={Heart} title="The mirroring rule">
        <p className="text-white/70 text-sm leading-relaxed">
          After every user message, Leilani <strong>mirrors what they said</strong> in
          1–3 sentences before moving to the next qualifier. Mirrors are compassionate,
          specific, and contain no advice, no diagnosis, and no clinical-speak. The
          goal is the client feeling <em>heard</em> before they feel steered. The bot
          never offers medical advice — it sets up a free discovery call with a real
          coach.
        </p>
      </Section>

      <Section icon={ListOrdered} title="The 9-step script">
        <div className="space-y-2">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="flex items-start gap-4 p-4 rounded-xl bg-white/[0.02] border border-white/5"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center text-sm font-semibold shrink-0">
                {s.n}
              </div>
              <div className="flex-1">
                <div className="text-sm text-white/85">{s.text}</div>
                <div className="text-[10px] uppercase tracking-wider text-white/40 mt-1">
                  emotional weight · {s.emotional}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section icon={Clock} title="Natural timing">
        <div className="grid sm:grid-cols-2 gap-3 text-sm text-white/70">
          <Bullet>30–120s per reply depending on message length</Bullet>
          <Bullet>High-emotion steps (4, 5, 7) wait 1.5× longer — space for the user to feel</Bullet>
          <Bullet>Typing indicator shown ~3s before the message lands</Bullet>
          <Bullet>Multi-message replies split, with ~1.5s gap between bubbles</Bullet>
        </div>
      </Section>

      <Section icon={Moon} title="Night mode">
        <p className="text-white/70 text-sm leading-relaxed">
          Between <strong>10pm and 8am</strong> local time the bot holds all outbound
          messages and releases them at 8am. Wellness messages at 3am don't feel right
          — and the clinic doesn't want to be that voice in someone's pocket.
        </p>
      </Section>

      <Section icon={HandMetal} title="Handoff">
        <div className="space-y-2 text-sm text-white/70">
          <Bullet>
            <strong>Urgent</strong> → keyword detection (active panic, self-harm,
            medical emergency) flips the conversation to{" "}
            <code className="text-violet-300">handed_off</code> and surfaces an urgent
            banner at the top of{" "}
            <a href="/conversations" className="text-violet-300 hover:text-violet-200">/conversations</a>.
            The bot does NOT offer medical advice — a teammate steps in.
          </Bullet>
          <Bullet>
            <strong>Dead-reengaged</strong> → if a conversation with &gt;6 messages
            goes quiet for 7+ days and the user writes back, the bot steps aside and
            marks it handed_off here for you to pick up.
          </Bullet>
          <Bullet>
            <strong>Manual</strong> → press <em>Take over</em> on any conversation;
            the bot stops answering until you press <em>Resume</em>.
          </Bullet>
        </div>
      </Section>

      <Section icon={Repeat} title="The correction + training loop">
        <p className="text-white/70 text-sm leading-relaxed">
          Every correction you save on <code className="text-violet-300">/corrections</code>{" "}
          and every example on <code className="text-violet-300">/training</code> is
          injected into Leilani's system prompt on the next Claude call. The bot reads
          them fresh each time — no re-training, no deploy, instant effect. This is
          how the clinic teaches the bot its specific voice over time.
        </p>
        <p className="text-white/70 text-sm leading-relaxed mt-3">
          Responses also go through a repetition-check: if a reply is too similar to
          anything already said, or repeats a question already asked, Claude is called
          up to 2 more times to regenerate before giving up.
        </p>
      </Section>

      <Section icon={MessageSquare} title="Practice mode">
        <p className="text-white/70 text-sm leading-relaxed">
          The <a href="/practice" className="text-violet-300 hover:text-violet-200">/practice</a>{" "}
          page is a sandbox — it uses the real prompt, real corrections, real training,
          real step logic. The only difference is the conversation is stored under a{" "}
          <code className="text-violet-300">practice_web_</code> namespace so it never
          mixes with real clients. Perfect for testing corrections you just added.
        </p>
      </Section>
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof Sparkles;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-700/10 border border-violet-400/20 flex items-center justify-center">
          <Icon className="w-4 h-4 text-violet-300" />
        </div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Bullet({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-2">
      <span className="text-violet-400 shrink-0">◆</span>
      <span>{children}</span>
    </div>
  );
}
