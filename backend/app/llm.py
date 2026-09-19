from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Hypothesis:
    cause: str
    confidence: str  # "high" | "medium" | "low"
    evidence: str


@dataclass
class AgentAction:
    """One reasoning step: either call a tool, or finish the investigation."""

    thought: str
    tool_name: str | None  # None means the agent is finishing
    tool_args: dict = field(default_factory=dict)
    hypotheses: list[Hypothesis] = field(default_factory=list)


class LLMClient(Protocol):
    def next_action(self, *, alert_title: str, alert_description: str, service_name: str, history: list[dict]) -> AgentAction: ...


class MockLLMClient:
    """Deterministic rule-based investigator used for local dev, tests, and CI.

    No network calls and no API key required. Swap in a real client (see
    `openai_client.py`) that implements the same `LLMClient` protocol when
    an API key is available.
    """

    def next_action(self, *, alert_title, alert_description, service_name, history):
        done = {h["tool_name"] for h in history}

        if "get_recent_deploys" not in done:
            return AgentAction(
                thought=f"Check whether {service_name} deployed recently — the most common cause of a sudden alert.",
                tool_name="get_recent_deploys",
                tool_args={"service_name": service_name},
            )

        if "get_error_logs" not in done:
            return AgentAction(
                thought="Pull recent error logs to see what's actually failing.",
                tool_name="get_error_logs",
                tool_args={"service_name": service_name},
            )

        if "search_past_incidents" not in done:
            return AgentAction(
                thought="Search past incidents on this service for a matching symptom signature.",
                tool_name="search_past_incidents",
                tool_args={"service_name": service_name, "query": alert_title},
            )

        if "get_service_dependencies" not in done:
            return AgentAction(
                thought="Check whether an upstream dependency is also degraded right now.",
                tool_name="get_service_dependencies",
                tool_args={"service_name": service_name},
            )

        return AgentAction(
            thought="Enough evidence gathered. Ranking hypotheses by strength of evidence.",
            tool_name=None,
            hypotheses=_rank_hypotheses(history),
        )


def _rank_hypotheses(history: list[dict]) -> list[Hypothesis]:
    by_tool = {h["tool_name"]: h["observation"] for h in history}
    hypotheses: list[Hypothesis] = []

    deploys = by_tool.get("get_recent_deploys", {}).get("deploys", [])
    if deploys:
        latest = deploys[0]
        hypotheses.append(Hypothesis(
            cause=f"Recent deploy {latest['commit_sha']} ({latest['description']}) likely introduced this.",
            confidence="high",
            evidence=f"Deployed at {latest['deployed_at']}, shortly before the alert fired.",
        ))

    past_matches = by_tool.get("search_past_incidents", {}).get("matches", [])
    if past_matches:
        match = past_matches[0]
        hypotheses.append(Hypothesis(
            cause=f"Same signature as a past incident: {match['root_cause']}",
            confidence="medium",
            evidence=f"Matched past incident: \"{match['signature']}\", resolved {match['resolved_at']}.",
        ))

    dependencies = by_tool.get("get_service_dependencies", {}).get("degraded_dependencies", [])
    if dependencies:
        hypotheses.append(Hypothesis(
            cause=f"Upstream dependency degraded: {', '.join(dependencies)}.",
            confidence="medium",
            evidence="Dependency service currently has its own open alert.",
        ))

    if not hypotheses:
        hypotheses.append(Hypothesis(
            cause="No strong signal found from deploys, past incidents, or dependencies.",
            confidence="low",
            evidence="Needs manual investigation — check logs and metrics directly.",
        ))

    return hypotheses
