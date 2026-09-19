"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchServices, type Service } from "@/lib/api";

export default function Services() {
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchServices().then(setServices).catch((err) => setError(err.message));
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to alerts
      </Link>
      <h1 className="mt-4 mb-1 text-2xl font-semibold">Services</h1>
      <p className="mb-8 text-zinc-500">
        The dependency graph the agent checks for cross-service degradation.
      </p>

      {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

      <div className="space-y-3">
        {services.map((s) => (
          <div key={s.id} className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="font-medium">{s.name}</p>
            <p className="text-sm text-zinc-500">owned by {s.owner_team}</p>
            {s.depends_on && (
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                depends on: {s.depends_on}
              </p>
            )}
          </div>
        ))}
        {services.length === 0 && <p className="text-zinc-500">No services yet.</p>}
      </div>
    </main>
  );
}
