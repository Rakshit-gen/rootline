"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchAlerts, investigateAlert, runsExportUrl, type Alert } from "@/lib/api";

const STATUS_STYLES: Record<Alert["status"], string> = {
  open: "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100",
  investigating: "bg-amber-200 text-amber-900 dark:bg-amber-800 dark:text-amber-100",
  resolved: "bg-emerald-200 text-emerald-900 dark:bg-emerald-800 dark:text-emerald-100",
};

const FILTERS: Array<{ label: string; value: Alert["status"] | "all" }> = [
  { label: "All", value: "all" },
  { label: "Open", value: "open" },
  { label: "Investigating", value: "investigating" },
  { label: "Resolved", value: "resolved" },
];

export default function Home() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [investigating, setInvestigating] = useState<number | null>(null);
  const [filter, setFilter] = useState<Alert["status"] | "all">("all");

  function reload() {
    fetchAlerts().then(setAlerts).catch((err) => setError(err.message));
  }

  useEffect(reload, []);

  const visibleAlerts = filter === "all" ? alerts : alerts.filter((a) => a.status === filter);

  async function handleInvestigate(id: number) {
    setInvestigating(id);
    try {
      await investigateAlert(id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setInvestigating(null);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold">rootline</h1>
        <p className="mt-1 text-zinc-600 dark:text-zinc-400">
          Agent correlates deploys, logs, past incidents, and dependencies into ranked root-cause hypotheses.
        </p>
        <div className="mt-2 flex gap-4 text-sm">
          <a href={runsExportUrl()} className="underline">
            Export investigation audit trail (CSV)
          </a>
          <Link href="/services" className="underline">
            Services
          </Link>
          <Link href="/history" className="underline">
            History
          </Link>
        </div>
      </header>

      {error && <p className="mb-4 text-red-600 dark:text-red-400">{error}</p>}

      <div className="mb-6 flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const count = f.value === "all" ? alerts.length : alerts.filter((a) => a.status === f.value).length;
          return (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`rounded-full px-3 py-1 text-sm ${
                filter === f.value
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "border border-zinc-300 dark:border-zinc-700"
              }`}
            >
              {f.label} ({count})
            </button>
          );
        })}
      </div>

      <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
        {visibleAlerts.map((a) => (
          <div key={a.id} className="flex items-center justify-between gap-4 py-4">
            <div>
              <Link href={`/alerts/${a.id}`} className="font-medium hover:underline">
                {a.title}
              </Link>
              <p className="text-sm text-zinc-500">{a.description}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLES[a.status]}`}>
                {a.status}
              </span>
              {a.status === "open" && (
                <button
                  onClick={() => handleInvestigate(a.id)}
                  disabled={investigating === a.id}
                  className="rounded border border-zinc-300 px-3 py-1 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  {investigating === a.id ? "Investigating..." : "Investigate"}
                </button>
              )}
            </div>
          </div>
        ))}
        {visibleAlerts.length === 0 && <p className="py-8 text-zinc-500">No alerts in this view.</p>}
      </div>
    </main>
  );
}
