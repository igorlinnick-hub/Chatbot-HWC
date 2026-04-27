"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  MessagesSquare,
  PencilLine,
  BookOpen,
  Sparkles,
  Cable,
  Info,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/conversations", label: "Conversations", icon: MessagesSquare },
  { href: "/practice", label: "Practice / Test", icon: Sparkles },
  { href: "/corrections", label: "Corrections", icon: PencilLine },
  { href: "/training", label: "Training", icon: BookOpen },
  { href: "/integrations", label: "Integrations", icon: Cable },
  { href: "/about", label: "About the Bot", icon: Info },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col p-5 border-r border-white/5 sticky top-0 h-screen">
      <div className="px-3 pt-2 pb-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-400 to-violet-700 shadow-lg shadow-violet-900/50 flex items-center justify-center">
            <span className="text-white font-bold text-sm">HW</span>
          </div>
          <div>
            <div className="text-white font-semibold">Hawaii Wellness</div>
            <div className="text-[11px] text-white/40 uppercase tracking-wider">Bot Dashboard</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                active
                  ? "bg-gradient-to-r from-violet-500/25 to-violet-500/5 text-white border border-violet-400/30 shadow-[0_0_25px_-10px_rgba(139,92,246,0.6)]"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={logout}
        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/5 transition-all"
      >
        <LogOut className="w-4 h-4" />
        Sign out
      </button>
    </aside>
  );
}
