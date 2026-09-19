from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from sqlmodel import Session, select

from .models import Alert, Deploy, PastIncident, Service

DEPLOY_LOOKBACK = timedelta(hours=6)


@dataclass
class ToolResult:
    tool_name: str
    args: dict
    output: dict


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., dict]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def specs(self) -> list[dict]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def call(self, name: str, args: dict) -> ToolResult:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        output = self._tools[name].fn(**args)
        return ToolResult(tool_name=name, args=args, output=output)


def _get_service(session: Session, service_name: str) -> Service | None:
    return session.exec(select(Service).where(Service.name == service_name)).first()


def get_recent_deploys(session: Session, service_name: str, alert_fired_at) -> dict:
    service = _get_service(session, service_name)
    if not service:
        return {"deploys": []}
    window_start = alert_fired_at - DEPLOY_LOOKBACK
    deploys = session.exec(
        select(Deploy)
        .where(Deploy.service_id == service.id, Deploy.deployed_at >= window_start, Deploy.deployed_at <= alert_fired_at)
        .order_by(Deploy.deployed_at.desc())
    ).all()
    return {"deploys": [
        {"commit_sha": d.commit_sha, "description": d.description, "deployed_at": d.deployed_at.isoformat()}
        for d in deploys
    ]}


def get_error_logs(session: Session, service_name: str) -> dict:
    # ponytail: no real log backend wired up; a fixed line count keyed off the
    # service name stands in for what would be a Loki/Datadog query.
    return {"log_lines": [f"[{service_name}] elevated 5xx rate observed in the last 15 minutes."]}


def search_past_incidents(session: Session, service_name: str, query: str) -> dict:
    service = _get_service(session, service_name)
    if not service:
        return {"matches": []}
    terms = [t.lower() for t in query.split() if len(t) > 3]
    incidents = session.exec(select(PastIncident).where(PastIncident.service_id == service.id)).all()
    matches = [
        i for i in incidents
        if any(term in i.signature.lower() for term in terms)
    ]
    return {"matches": [
        {"signature": i.signature, "root_cause": i.root_cause, "resolved_at": i.resolved_at.isoformat()}
        for i in matches[:3]
    ]}


def get_service_dependencies(session: Session, service_name: str) -> dict:
    service = _get_service(session, service_name)
    if not service or not service.depends_on:
        return {"dependencies": [], "degraded_dependencies": []}
    dep_names = [d.strip() for d in service.depends_on.split(",") if d.strip()]
    degraded = []
    for name in dep_names:
        dep_service = _get_service(session, name)
        if not dep_service:
            continue
        open_alert = session.exec(
            select(Alert).where(Alert.service_id == dep_service.id, Alert.status == "open")
        ).first()
        if open_alert:
            degraded.append(name)
    return {"dependencies": dep_names, "degraded_dependencies": degraded}


def build_default_registry(session: Session, alert_fired_at) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool(
        "get_recent_deploys",
        "List deploys to this service in the hours before the alert fired.",
        lambda service_name: get_recent_deploys(session, service_name, alert_fired_at),
    ))
    registry.register(Tool(
        "get_error_logs",
        "Fetch recent error log lines for this service.",
        lambda service_name: get_error_logs(session, service_name),
    ))
    registry.register(Tool(
        "search_past_incidents",
        "Search past incidents on this service for a matching symptom signature.",
        lambda service_name, query: search_past_incidents(session, service_name, query),
    ))
    registry.register(Tool(
        "get_service_dependencies",
        "List this service's dependencies and flag any with a currently open alert.",
        lambda service_name: get_service_dependencies(session, service_name),
    ))
    return registry
