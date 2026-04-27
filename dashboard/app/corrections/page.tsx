import { listCorrections } from "@/lib/data";
import CorrectionForm from "@/components/correction-form";
import DeleteButton from "@/components/delete-button";
import { formatDate } from "@/lib/utils";
import { PencilLine } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function CorrectionsPage() {
  const list = await listCorrections();

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <header>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-violet-300/70 mb-2">
          Feedback Loop
        </div>
        <h1 className="text-4xl font-semibold glow-text">Corrections</h1>
        <p className="text-white/50 mt-2">
          Saved rewrites of bot responses — injected into the system prompt as examples of
          what to do instead.
        </p>
      </header>

      <CorrectionForm />

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wider text-white/40">
          {list.length} correction{list.length === 1 ? "" : "s"}
        </h2>
        {list.length === 0 && (
          <div className="card text-white/40 text-center py-10">
            <PencilLine className="w-6 h-6 mx-auto mb-3 opacity-50" />
            No corrections yet.
          </div>
        )}
        {list.map((c) => (
          <div key={c.id} className="card card-hover space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div className="text-xs text-white/40">{formatDate(c.created_at)}</div>
              <DeleteButton id={c.id} kind="corrections" />
            </div>
            <div>
              <div className="label">User said</div>
              <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white/80">
                {c.context}
              </div>
            </div>
            <div>
              <div className="label text-red-300/70">Bot originally said ❌</div>
              <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-3 text-sm text-white/70 line-through">
                {c.original_response}
              </div>
            </div>
            <div>
              <div className="label text-emerald-300/70">Should have said ✓</div>
              <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-3 text-sm text-white/90">
                {c.corrected_response}
              </div>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
