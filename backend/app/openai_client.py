"""Optional real LLM-backed investigator.

Not used unless OPENAI_API_KEY is set — the engine falls back to
MockLLMClient otherwise, so the project runs and tests fully offline.
"""

from __future__ import annotations

import json
import os
import urllib.request

from .llm import AgentAction, Hypothesis

SYSTEM_PROMPT = (
    "You are an incident investigation agent. Given an alert and the results of "
    "tools already called, respond with JSON: "
    '{"thought": str, "tool_name": str | null, "tool_args": object, '
    '"hypotheses": [{"cause": str, "confidence": "high"|"medium"|"low", "evidence": str}]}. '
    "Set tool_name to null only when finishing, at which point hypotheses must be "
    "non-empty and ranked strongest first. Prefer checking deploys, then error logs, "
    "then past incidents, then dependencies, before concluding."
)


class OpenAIClient:
    """Real LLM-backed investigator. Requires OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]

    def next_action(self, *, alert_title, alert_description, service_name, history) -> AgentAction:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps({
                    "alert_title": alert_title,
                    "alert_description": alert_description,
                    "service_name": service_name,
                    "history": history,
                })},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read())
        content = json.loads(body["choices"][0]["message"]["content"])
        return AgentAction(
            thought=content.get("thought", ""),
            tool_name=content.get("tool_name"),
            tool_args=content.get("tool_args") or {},
            hypotheses=[Hypothesis(**h) for h in content.get("hypotheses") or []],
        )


def get_llm_client():
    """Real client if OPENAI_API_KEY is set, else the deterministic mock."""
    from .llm import MockLLMClient

    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIClient()
    return MockLLMClient()
