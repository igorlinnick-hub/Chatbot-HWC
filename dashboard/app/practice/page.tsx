import PracticeChat from "@/components/practice-chat";
import { Sparkles } from "lucide-react";

export default function PracticePage() {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <header>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
          Practice Mode
        </div>
        <h1 className="text-4xl font-semibold glow-text">Test the bot</h1>
        <p className="text-white/50 mt-2">
          Roleplay a conversation as a prospective client. Same prompt, same script, but
          nothing saved to real conversations. Great for testing corrections you just added.
        </p>
      </header>

      <div className="card bg-gradient-to-br from-violet-500/5 to-transparent border-violet-400/20">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-violet-300 shrink-0 mt-0.5" />
          <div className="text-sm text-white/70">
            Start typing below. Your first message triggers the step-1 opener, just like a
            real DM. Type <code className="text-violet-300">/reset</code> to start over.
          </div>
        </div>
      </div>

      <PracticeChat />
    </div>
  );
}
