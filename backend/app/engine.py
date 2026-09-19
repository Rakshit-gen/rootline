from dataclasses import asdict
from datetime import datetime, timezone

from sqlmodel import Session

from .llm import LLMClient
from .models import Alert, AgentRun, AgentStep, Service
from .openai_client import get_llm_client
from .tools import build_default_registry

MAX_STEPS = 6


def run_agent(session: Session, alert: Alert, llm: LLMClient | None = None) -> AgentRun:
    """Drive one alert through the observe -> plan -> act loop until the
    investigator finishes with a ranked list of hypotheses.
    """
    llm = llm or get_llm_client()
    registry = build_default_registry(session, alert.fired_at)
    service = session.get(Service, alert.service_id)

    run = AgentRun(alert_id=alert.id)
    session.add(run)
    session.commit()
    session.refresh(run)

    history: list[dict] = []

    for step_number in range(1, MAX_STEPS + 1):
        action = llm.next_action(
            alert_title=alert.title,
            alert_description=alert.description,
            service_name=service.name,
            history=history,
        )

        if action.tool_name is None:
            run.status = "completed"
            run.hypotheses = [asdict(h) for h in action.hypotheses]
            run.decided_at = datetime.now(timezone.utc)
            session.add(run)
            session.add(AgentStep(
                run_id=run.id, step_number=step_number, thought=action.thought,
                tool_name="", tool_args={}, observation={},
            ))
            session.commit()
            session.refresh(run)
            return run

        result = registry.call(action.tool_name, action.tool_args)
        session.add(AgentStep(
            run_id=run.id, step_number=step_number, thought=action.thought,
            tool_name=action.tool_name, tool_args=action.tool_args, observation=result.output,
        ))
        session.commit()
        history.append({"tool_name": action.tool_name, "observation": result.output})

    run.status = "completed"
    run.hypotheses = [{"cause": "Step budget exhausted before a conclusion.", "confidence": "low", "evidence": ""}]
    run.decided_at = datetime.now(timezone.utc)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run
