"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchDeploys, fetchIncidents, fetchServices, type Deploy, type PastIncident, type Service } from "@/lib/api";

export default function History() {
  const [deploys, setDeploys] = useState<Deploy[]>([]);
  const [incidents, setIncidents] = useState<PastIncident[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchDeploys(), fetchIncidents(), fetchServices()])
      .then(([d, i, s]) => {
        setDeploys(d);
        setIncidents(i);
        setServices(s);
      })
      .catch((err) => setError(err.message));
  }, []);

  const serviceName = (id: number) => services.find((s) => s.id === id)?.name ?? `service #${id}`;

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to alerts
      </Link>
      <h1 className="mt-4 mb-1 text-2xl font-semibold">History</h1>
      <p className="mb-8 text-zinc-500">
        Recent deploys and past incidents the agent searches during an investigation.
      </p>

      {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

      <h2 className="mb-3 text-lg font-medium">Deploys</h2>
      <div className="mb-8 space-y-3">
        {deploys.map((d) => (
          <div key={d.id} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
            <p className="font-medium">{serviceName(d.service_id)} · {d.commit_sha}</p>
            <p className="text-zinc-600 dark:text-zinc-400">{d.description}</p>
            <p className="mt-1 text-xs text-zinc-500">{new Date(d.deployed_at).toLocaleString()}</p>
          </div>
        ))}
        {deploys.length === 0 && <p className="text-zinc-500">No deploys yet.</p>}
      </div>

      <h2 className="mb-3 text-lg font-medium">Past incidents</h2>
      <div className="space-y-3">
        {incidents.map((i) => (
          <div key={i.id} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
            <p className="font-medium">{serviceName(i.service_id)}: {i.signature}</p>
            <p className="text-zinc-600 dark:text-zinc-400">{i.root_cause}</p>
            <p className="mt-1 text-xs text-zinc-500">resolved {new Date(i.resolved_at).toLocaleString()}</p>
          </div>
        ))}
        {incidents.length === 0 && <p className="text-zinc-500">No past incidents yet.</p>}
      </div>
    </main>
  );
}
