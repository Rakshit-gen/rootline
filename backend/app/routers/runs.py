import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ..db import get_session
from ..engine import run_agent
from ..models import Alert, AgentRun
from ..schemas import AgentRunRead, ConfirmHypothesis

router = APIRouter(tags=["runs"])


@router.get("/runs/", response_model=list[AgentRunRead])
def list_runs(session: Session = Depends(get_session)):
    return session.exec(select(AgentRun).order_by(AgentRun.started_at.desc())).all()


@router.get("/runs/export/")
def export_runs_csv(session: Session = Depends(get_session)):
    """Downloadable audit trail of every investigation, for an incident review doc."""
    runs = session.exec(select(AgentRun).order_by(AgentRun.started_at.desc())).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["run_id", "alert_id", "status", "top_hypothesis", "confirmed_hypothesis", "started_at", "decided_at"])
    for run in runs:
        top = run.hypotheses[0]["cause"] if run.hypotheses else ""
        writer.writerow([run.id, run.alert_id, run.status, top, run.confirmed_hypothesis or "", run.started_at, run.decided_at])
    buffer.seek(0)

    return StreamingResponse(
        buffer, media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="rootline_agent_runs.csv"'},
    )


@router.get("/runs/{run_id}/", response_model=AgentRunRead)
def get_run(run_id: int, session: Session = Depends(get_session)):
    run = session.get(AgentRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    return run


@router.post("/alerts/{alert_id}/investigate/", response_model=AgentRunRead, status_code=201)
def investigate_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found.")
    alert.status = "investigating"
    session.add(alert)
    session.commit()
    return run_agent(session, alert)


@router.post("/runs/{run_id}/confirm/", response_model=AgentRunRead)
def confirm_hypothesis(run_id: int, payload: ConfirmHypothesis, session: Session = Depends(get_session)):
    run = session.get(AgentRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    run.confirmed_hypothesis = payload.cause
    session.add(run)

    alert = session.get(Alert, run.alert_id)
    alert.status = "resolved"
    session.add(alert)

    session.commit()
    session.refresh(run)
    return run
