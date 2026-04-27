"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { Trash2, Loader2 } from "lucide-react";

export default function DeleteButton({
  id,
  kind,
}: {
  id: string;
  kind: "corrections" | "training";
}) {
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  function del() {
    if (!confirm("Delete this? This cannot be undone.")) return;
    startTransition(async () => {
      await fetch(`/api/${kind}?id=${id}`, { method: "DELETE" });
      router.refresh();
    });
  }

  return (
    <button
      onClick={del}
      disabled={pending}
      className="text-white/30 hover:text-red-300 transition-colors"
      aria-label="Delete"
    >
      {pending ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Trash2 className="w-4 h-4" />
      )}
    </button>
  );
}
