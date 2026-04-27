import { listTraining } from "@/lib/data";
import TrainingForm from "@/components/training-form";
import DeleteButton from "@/components/delete-button";
import { formatDate } from "@/lib/utils";
import { BookOpen } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function TrainingPage() {
  const list = await listTraining();

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <header>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
          Teaching Examples
        </div>
        <h1 className="text-4xl font-semibold glow-text">Training</h1>
        <p className="text-white/50 mt-2">
          Gold-standard user-message / ideal-response pairs. The bot rotates the most
          relevant examples into its system prompt on each call.
        </p>
      </header>

      <TrainingForm />

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wider text-white/40">
          {list.length} example{list.length === 1 ? "" : "s"}
        </h2>
        {list.length === 0 && (
          <div className="card text-white/40 text-center py-10">
            <BookOpen className="w-6 h-6 mx-auto mb-3 opacity-50" />
            No training examples yet.
          </div>
        )}
        {list.map((t) => (
          <div key={t.id} className="card card-hover space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div className="text-xs text-white/40">{formatDate(t.created_at)}</div>
              <DeleteButton id={t.id} kind="training" />
            </div>
            <div>
              <div className="label">User message</div>
              <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white/80">
                {t.user_message}
              </div>
            </div>
            <div>
              <div className="label text-violet-300/70">Ideal response</div>
              <div className="bg-violet-500/5 border border-violet-400/20 rounded-xl p-3 text-sm text-white/90">
                {t.ideal_response}
              </div>
            </div>
            {t.notes && (
              <div>
                <div className="label">Notes</div>
                <div className="text-sm text-white/60 italic">{t.notes}</div>
              </div>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}
