from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Alert, Service
from ..schemas import AlertCreate, AlertRead

router = APIRouter(tags=["alerts"])


@router.get("/alerts/", response_model=list[AlertRead])
def list_alerts(session: Session = Depends(get_session)):
    return session.exec(select(Alert).order_by(Alert.fired_at.desc())).all()


@router.get("/alerts/{alert_id}/", response_model=AlertRead)
def get_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found.")
    return alert


@router.post("/alerts/", response_model=AlertRead, status_code=201)
def create_alert(payload: AlertCreate, session: Session = Depends(get_session)):
    if not session.get(Service, payload.service_id):
        raise HTTPException(404, "Service not found.")
    alert = Alert(**payload.model_dump())
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert
