# rootline

An agentic incident investigation assistant that automates the first ten
minutes of an on-call page: correlating deploys, logs, past incidents, and
service dependencies into a ranked, evidence-backed list of root-cause
hypotheses.

## The problem

PagerDuty and Opsgenie tell you *that* something broke. They don't tell
you *why*. The engineer who gets paged still has to manually check "did we
deploy recently," grep logs, remember whether this looks like a past
incident, and check whether an upstream dependency is also down — all
before they've written a single line of code. That's dead time on every
page, and it's the same four checks every time.

`rootline` automates exactly those four checks and nothing else. It
doesn't touch your infrastructure, restart anything, or page anyone; it
gathers evidence and ranks hypotheses so the human starts debugging with
a head start instead of a blank page.

## How the agent works

Each alert runs through an observe → plan → act loop, persisted step by
step:

1. **get_recent_deploys** — did this service deploy in the hours before
   the alert fired?
2. **get_error_logs** — what's actually failing right now?
3. **search_past_incidents** — has this exact symptom happened before, and
   what was the root cause that time?
4. **get_service_dependencies** — is an upstream dependency also
   currently alerting?

The planner (`LLMClient`) is a protocol, not a hardcoded call. By default
it's `MockLLMClient` — deterministic, rule-based, no network calls, no API
key — so the project runs and its test suite passes with zero setup. Set
`OPENAI_API_KEY` and the engine switches to `OpenAIClient`, which asks a
real model for the same JSON-shaped decision at each step. The loop, the
tools, and the audit trail don't change — only the planner does.

Hypotheses are ranked by evidence strength (a recent deploy outranks a
vague past-incident match), and a human explicitly confirms which one was
actually the cause — that confirmation is what resolves the alert, not
the agent's own confidence score.

## Stack

- **Backend**: FastAPI + SQLModel, SQLite for local/demo use.
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind.

## Running locally

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Open the frontend, click "Investigate" on an open alert, and read the
trace before confirming which hypothesis was the real root cause. Set
`OPENAI_API_KEY` in the backend's environment to use a real model instead
of the deterministic mock planner.

## What's not built

No live integration with a real APM/log backend (Datadog, Honeycomb,
Loki) — `get_error_logs` is a stand-in for what would be a real query.
No automatic remediation or rollback; this investigates, it doesn't act.
No alerting webhook ingestion from PagerDuty/Opsgenie — alerts are
created directly in the app for the same reason tickets are in
`triagepilot`: the agent loop is the point, not the integration surface.
