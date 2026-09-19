"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  confirmHypothesis,
  fetchAlert,
  fetchRuns,
  investigateAlert,
  type Alert,
  type AgentRun,
} from "@/lib/api";

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "border-red-400 dark:border-red-700",
  medium: "border-amber-400 dark:border-amber-700",
  low: "border-zinc-300 dark:border-zinc-700",
};

export default function AlertDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const alertId = Number(id);

  const [alert, setAlert] = useState<Alert | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reload() {
    fetchAlert(alertId).then(setAlert).catch((err) => setError(err.message));
    fetchRuns()
      .then((all) => setRuns(all.filter((r) => r.alert_id === alertId)))
      .catch((err) => setError(err.message));
  }

  useEffect(reload, [alertId]);

  const latestRun = runs[0];

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!alert) return <main className="mx-auto max-w-3xl px-5 py-10">Loading…</main>;

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to alerts
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{alert.title}</h1>
      <p className="text-zinc-500">status: {alert.status}</p>
      <p className="mt-4 rounded border border-zinc-200 p-4 dark:border-zinc-800">{alert.description}</p>

      {error && <p className="mt-4 text-red-600 dark:text-red-400">{error}</p>}

      {alert.status === "open" && (
        <button
          onClick={() => run(() => investigateAlert(alertId))}
          disabled={busy}
          className="mt-6 rounded border border-zinc-300 px-4 py-2 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
        >
          Investigate
        </button>
      )}

      {latestRun && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">Investigation trace</h2>
          <ol className="space-y-3">
            {latestRun.steps.map((step) => (
              <li key={step.id} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                <p className="font-medium">
                  Step {step.step_number}
                  {step.tool_name && ` · ${step.tool_name}`}
                </p>
                <p className="text-zinc-600 dark:text-zinc-400">{step.thought}</p>
                {step.tool_name && (
                  <pre className="mt-2 overflow-x-auto rounded bg-zinc-100 p-2 text-xs dark:bg-zinc-900">
                    {JSON.stringify(step.observation, null, 2)}
                  </pre>
                )}
              </li>
            ))}
          </ol>

          <h2 className="mt-6 mb-3 text-lg font-medium">Ranked hypotheses</h2>
          <div className="space-y-3">
            {latestRun.hypotheses.map((h, i) => (
              <div
                key={i}
                className={`rounded border-l-4 bg-zinc-50 p-3 text-sm dark:bg-zinc-900 ${CONFIDENCE_STYLES[h.confidence]}`}
              >
                <p className="font-medium">
                  {h.cause}{" "}
                  <span className="font-normal text-zinc-500">({h.confidence} confidence)</span>
                </p>
                <p className="mt-1 text-zinc-600 dark:text-zinc-400">{h.evidence}</p>
                {alert.status !== "resolved" && (
                  <button
                    onClick={() => run(() => confirmHypothesis(latestRun.id, h.cause))}
                    disabled={busy}
                    className="mt-2 rounded bg-emerald-600 px-3 py-1 text-xs text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    Confirm as root cause
                  </button>
                )}
              </div>
            ))}
          </div>

          {latestRun.confirmed_hypothesis && (
            <p className="mt-4 rounded border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
              Confirmed root cause: {latestRun.confirmed_hypothesis}
            </p>
          )}
        </section>
      )}
    </main>
  );
}
