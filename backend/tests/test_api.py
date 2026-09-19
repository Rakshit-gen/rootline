from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_service_and_alert_then_investigate(client):
    service_resp = client.post("/api/services/", json={"name": "checkout", "owner_team": "commerce"})
    assert service_resp.status_code == 201
    service_id = service_resp.json()["id"]

    alert_resp = client.post("/api/alerts/", json={
        "service_id": service_id, "title": "5xx spike", "description": "",
        "fired_at": datetime.now(timezone.utc).isoformat(),
    })
    assert alert_resp.status_code == 201
    alert_id = alert_resp.json()["id"]

    run_resp = client.post(f"/api/alerts/{alert_id}/investigate/")
    assert run_resp.status_code == 201
    run = run_resp.json()
    assert run["status"] == "completed"
    assert len(run["hypotheses"]) >= 1

    alert_after = client.get(f"/api/alerts/{alert_id}/").json()
    assert alert_after["status"] == "investigating"


def test_investigate_missing_alert_404s(client):
    resp = client.post("/api/alerts/999/investigate/")
    assert resp.status_code == 404


def test_confirm_hypothesis_resolves_the_alert(client):
    service_id = client.post("/api/services/", json={"name": "auth", "owner_team": "identity"}).json()["id"]
    alert_id = client.post("/api/alerts/", json={
        "service_id": service_id, "title": "auth errors", "description": "",
        "fired_at": datetime.now(timezone.utc).isoformat(),
    }).json()["id"]
    run_id = client.post(f"/api/alerts/{alert_id}/investigate/").json()["id"]

    confirm_resp = client.post(f"/api/runs/{run_id}/confirm/", json={"cause": "manual root cause"})
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["confirmed_hypothesis"] == "manual root cause"

    alert_after = client.get(f"/api/alerts/{alert_id}/").json()
    assert alert_after["status"] == "resolved"


def test_cannot_reinvestigate_a_resolved_alert(client):
    service_id = client.post("/api/services/", json={"name": "payments", "owner_team": "commerce"}).json()["id"]
    alert_id = client.post("/api/alerts/", json={
        "service_id": service_id, "title": "payment errors", "description": "",
        "fired_at": datetime.now(timezone.utc).isoformat(),
    }).json()["id"]
    run_id = client.post(f"/api/alerts/{alert_id}/investigate/").json()["id"]
    client.post(f"/api/runs/{run_id}/confirm/", json={"cause": "manual root cause"})

    resp = client.post(f"/api/alerts/{alert_id}/investigate/")
    assert resp.status_code == 409


def test_create_deploy_requires_existing_service(client):
    resp = client.post("/api/deploys/", json={
        "service_id": 999, "commit_sha": "abc", "description": "x",
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    })
    assert resp.status_code == 404
