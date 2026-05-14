"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpenText, Bot, Brain, Code2, Layers3, Settings2, Sparkles } from "lucide-react";

import { appConfig } from "@/lib/config";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/", label: "Chat", icon: Sparkles },
  { href: "/code-agent", label: "Code Agent", icon: Code2 },
  { href: "/knowledge-bases", label: "Knowledge", icon: BookOpenText },
  { href: "/memories", label: "Memory", icon: Brain },
  { href: "/settings", label: "Settings", icon: Settings2 },
  { href: "/developer", label: "Developer", icon: Layers3 },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-transparent">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 gap-6 px-4 py-4 md:px-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:px-8 lg:py-8">
        <aside className="rounded-[1.8rem] border border-white/70 bg-slate-950 px-5 py-6 text-slate-100 shadow-[0_24px_60px_rgba(15,23,42,0.22)]">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-white/10 p-2.5">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-slate-300">Local Assistant</p>
              <h1 className="text-base font-semibold">{appConfig.appName}</h1>
            </div>
          </div>

          <nav className="mt-8 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                    isActive
                      ? "bg-white text-slate-950 shadow-soft"
                      : "text-slate-300 hover:bg-white/8 hover:text-white",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Portfolio Build</p>
            <p className="mt-2 text-sm leading-6 text-slate-200">
              Local chat, knowledge-base retrieval, explicit memory, diagnostics, SDK examples,
              and LAN-ready demo configuration are wired into one runnable product.
            </p>
          </div>
        </aside>

        <div className="flex min-h-full flex-col gap-6">{children}</div>
      </div>
    </div>
  );
}
