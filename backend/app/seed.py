"""Seed a small, reproducible demo dataset. Run with: python -m app.seed"""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from .db import engine, init_db
from .models import Alert, Deploy, PastIncident, Service


def get_or_create_service(session: Session, name: str, owner_team: str, depends_on: str = "") -> Service:
    existing = session.exec(select(Service).where(Service.name == name)).first()
    if existing:
        return existing
    service = Service(name=name, owner_team=owner_team, depends_on=depends_on)
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


def run() -> None:
    init_db()
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        auth = get_or_create_service(session, "auth", "identity")
        checkout = get_or_create_service(session, "checkout", "commerce", depends_on="auth,payments")
        payments = get_or_create_service(session, "payments", "commerce")

        session.add(Deploy(
            service_id=checkout.id, commit_sha="a1b2c3d", description="bump payment SDK to v4",
            deployed_at=now - timedelta(minutes=25),
        ))
        session.add(PastIncident(
            service_id=checkout.id, signature="5xx spike on checkout",
            root_cause="payment SDK v3 leaked connections under load",
            resolved_at=now - timedelta(days=45),
        ))
        session.add(Alert(
            service_id=checkout.id, title="5xx spike on checkout",
            description="Error rate on /checkout jumped from 0.1% to 8% in the last 10 minutes.",
            fired_at=now,
        ))
        session.add(Alert(
            service_id=auth.id, title="auth latency degraded",
            description="p99 login latency up 4x.",
            status="open", fired_at=now - timedelta(minutes=5),
        ))
        session.commit()

    print("Seeded demo services, a deploy, a past incident, and two alerts.")


if __name__ == "__main__":
    run()
