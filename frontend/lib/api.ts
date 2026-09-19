const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api";

export type Service = {
  id: number;
  name: string;
  owner_team: string;
  depends_on: string;
};

export type Alert = {
  id: number;
  service_id: number;
  title: string;
  description: string;
  status: "open" | "investigating" | "resolved";
  fired_at: string;
};

export type Deploy = {
  id: number;
  service_id: number;
  commit_sha: string;
  description: string;
  deployed_at: string;
};

export type PastIncident = {
  id: number;
  service_id: number;
  signature: string;
  root_cause: string;
  resolved_at: string;
};

export type Hypothesis = {
  cause: string;
  confidence: "high" | "medium" | "low";
  evidence: string;
};

export type AgentStep = {
  id: number;
  step_number: number;
  thought: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  observation: Record<string, unknown>;
};

export type AgentRun = {
  id: number;
  alert_id: number;
  status: "running" | "completed";
  hypotheses: Hypothesis[];
  confirmed_hypothesis: string | null;
  started_at: string;
  decided_at: string | null;
  steps: AgentStep[];
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export const fetchAlerts = () => getJson<Alert[]>("/alerts/");
export const fetchAlert = (id: number) => getJson<Alert>(`/alerts/${id}/`);
export const fetchServices = () => getJson<Service[]>("/services/");
export const fetchDeploys = () => getJson<Deploy[]>("/deploys/");
export const fetchIncidents = () => getJson<PastIncident[]>("/incidents/");
export const fetchRuns = () => getJson<AgentRun[]>("/runs/");

export const investigateAlert = (alertId: number) =>
  postJson<AgentRun>(`/alerts/${alertId}/investigate/`);

export const confirmHypothesis = (runId: number, cause: string) =>
  postJson<AgentRun>(`/runs/${runId}/confirm/`, { cause });

export const runsExportUrl = () => `${API_BASE}/runs/export/`;
