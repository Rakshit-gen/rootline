from datetime import datetime, timezone, timedelta

from app.engine import run_agent
from app.models import Alert, Deploy, PastIncident, Service


def make_service(session, name, depends_on="") -> Service:
    service = Service(name=name, owner_team="platform", depends_on=depends_on)
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


def test_recent_deploy_is_top_hypothesis(session):
    checkout = make_service(session, "checkout")
    fired_at = datetime.now(timezone.utc)
    session.add(Deploy(
        service_id=checkout.id, commit_sha="abc123", description="bump payment SDK",
        deployed_at=fired_at - timedelta(minutes=20),
    ))
    session.commit()

    alert = Alert(
        service_id=checkout.id, title="5xx spike", description="checkout returning 500s",
        fired_at=fired_at,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)

    run = run_agent(session, alert)
    assert run.status == "completed"
    assert "abc123" in run.hypotheses[0]["cause"]
    assert run.hypotheses[0]["confidence"] == "high"


def test_matches_past_incident_signature(session):
    checkout = make_service(session, "checkout")
    fired_at = datetime.now(timezone.utc)
    session.add(PastIncident(
        service_id=checkout.id, signature="5xx spike on checkout",
        root_cause="database connection pool exhaustion", resolved_at=fired_at - timedelta(days=10),
    ))
    session.commit()

    alert = Alert(service_id=checkout.id, title="5xx spike", description="", fired_at=fired_at)
    session.add(alert)
    session.commit()
    session.refresh(alert)

    run = run_agent(session, alert)
    causes = [h["cause"] for h in run.hypotheses]
    assert any("connection pool exhaustion" in c for c in causes)


def test_degraded_dependency_is_flagged(session):
    auth = make_service(session, "auth")
    checkout = make_service(session, "checkout", depends_on="auth")
    fired_at = datetime.now(timezone.utc)

    session.add(Alert(service_id=auth.id, title="auth errors", description="", status="open", fired_at=fired_at))
    session.commit()

    alert = Alert(service_id=checkout.id, title="checkout failing", description="", fired_at=fired_at)
    session.add(alert)
    session.commit()
    session.refresh(alert)

    run = run_agent(session, alert)
    causes = [h["cause"] for h in run.hypotheses]
    assert any("auth" in c for c in causes)


def test_no_signal_falls_back_to_low_confidence(session):
    lonely = make_service(session, "lonely-service")
    fired_at = datetime.now(timezone.utc)
    alert = Alert(service_id=lonely.id, title="mystery alert", description="", fired_at=fired_at)
    session.add(alert)
    session.commit()
    session.refresh(alert)

    run = run_agent(session, alert)
    assert run.hypotheses[0]["confidence"] == "low"


def test_every_step_is_recorded(session):
    lonely = make_service(session, "lonely-service")
    fired_at = datetime.now(timezone.utc)
    alert = Alert(service_id=lonely.id, title="mystery alert", description="", fired_at=fired_at)
    session.add(alert)
    session.commit()
    session.refresh(alert)

    run = run_agent(session, alert)
    tool_sequence = [s.tool_name for s in run.steps]
    assert tool_sequence == [
        "get_recent_deploys", "get_error_logs", "search_past_incidents", "get_service_dependencies", "",
    ]
