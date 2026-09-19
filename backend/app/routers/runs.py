from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..engine import run_agent
from ..models import Alert, AgentRun
from ..schemas import AgentRunRead, ConfirmHypothesis

router = APIRouter(tags=["runs"])


@router.get("/runs/", response_model=list[AgentRunRead])
def list_runs(session: Session = Depends(get_session)):
    return session.exec(select(AgentRun).order_by(AgentRun.started_at.desc())).all()


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
