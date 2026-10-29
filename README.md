# rootline

Does the first ten minutes of an on-call page for you. When an alert fires, rootline checks whether the service was just deployed, what is failing, whether this has happened before and whether something upstream is also down. It then gives you a ranked list of likely causes, each with the evidence behind it.

It only reads. It does not restart, roll back or page anyone.

## Why

PagerDuty and Opsgenie tell you that something broke, not why. The person who gets paged still runs the same four checks by hand every time: did we deploy, what do the logs say, have we seen this before, is a dependency down. rootline runs exactly those four checks and hands you the results, so you start debugging with evidence instead of a blank page.

## How it works

Each investigation runs a loop of up to 6 steps. The planner picks one tool per step:

| Tool | What it returns |
|---|---|
| `get_recent_deploys` | Deploys to this service in the 6 hours before the alert fired |
| `get_error_logs` | Recent error lines for the service (a stub today, see Limits) |
| `search_past_incidents` | Up to 3 past incidents on this service whose signature shares words with the alert title, with their root cause |
| `get_service_dependencies` | This service's dependencies, and which of them have an open alert right now |

When it has enough, the planner finishes with ranked hypotheses:

| Evidence | Confidence |
|---|---|
| A deploy shortly before the alert | high |
| A matching past incident | medium |
| A dependency with an open alert | medium |
| Nothing found | low, "no strong signal" |

A deploy ranks first because it is the most common cause and the easiest to act on.

Every step is saved with the planner's thought, the tool, its input and its output. The alert is only resolved when a person confirms which hypothesis was the real cause. The agent's own confidence never closes anything.

### Two planners, one loop

The planner is an interface (`backend/app/llm.py`):

- **`MockLLMClient`** (default). Runs the four checks in order and ranks with the table above. No network, no key, deterministic, so tests pass offline.
- **`OpenAIClient`**. Used when `OPENAI_API_KEY` is set. Sends the alert and step history to `gpt-4o-mini` and asks for the next action as JSON.

## Quickstart

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Frontend, in another terminal:

```bash
cd frontend
cp env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000, click **Investigate** on an open alert, read the trace, then confirm which hypothesis was right.

## Configuration

| Variable | Where | Default | What it does |
|---|---|---|---|
| `OPENAI_API_KEY` | backend | unset | Switches to the OpenAI planner |
| `DATABASE_URL` | backend | `sqlite:///./rootline.db` | Any SQLAlchemy URL |
| `NEXT_PUBLIC_API_BASE` | frontend | `http://127.0.0.1:8000/api` | Backend URL |

## API

All under `/api`.

| Method | Path | What it does |
|---|---|---|
| `POST` | `/alerts/{id}/investigate/` | Run an investigation, returns the run with steps and hypotheses |
| `POST` | `/runs/{id}/confirm/` | Body `{"cause": "..."}`. Records the real cause and resolves the alert |
| `GET` | `/runs/`, `/runs/{id}/` | Read runs |
| `GET` | `/runs/export/` | All runs as CSV |
| `GET`, `POST` | `/alerts/` | List or create alerts |
| `GET`, `POST` | `/services/`, `/deploys/`, `/incidents/` | The data the tools read |

## Layout

```
backend/app/engine.py         the investigation loop
backend/app/llm.py            planner interface, mock planner, hypothesis ranking
backend/app/openai_client.py  OpenAI planner
backend/app/tools.py          the four checks
backend/app/seed.py           demo services, deploys, incidents and alerts
backend/app/routers/          HTTP routes
backend/tests/                engine, API and planner selection tests
frontend/app/                 open alerts, investigation view, history, services
```

Tests: `cd backend && pytest`.

## Limits

- `get_error_logs` returns a fixed line. There is no Loki, Datadog or Honeycomb connection yet.
- Past incident search is word overlap with the alert title, not semantic search.
- Alerts are created in the app. There is no PagerDuty or Opsgenie webhook.
- Investigation only. No remediation or rollback, on purpose.
- SQLite and no auth by default.
