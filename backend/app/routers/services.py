from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Deploy, PastIncident, Service
from ..schemas import DeployCreate, DeployRead, PastIncidentCreate, PastIncidentRead, ServiceCreate, ServiceRead

router = APIRouter(tags=["services"])


@router.get("/services/", response_model=list[ServiceRead])
def list_services(session: Session = Depends(get_session)):
    return session.exec(select(Service).order_by(Service.name)).all()


@router.post("/services/", response_model=ServiceRead, status_code=201)
def create_service(payload: ServiceCreate, session: Session = Depends(get_session)):
    service = Service(**payload.model_dump())
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@router.get("/deploys/", response_model=list[DeployRead])
def list_deploys(session: Session = Depends(get_session)):
    return session.exec(select(Deploy).order_by(Deploy.deployed_at.desc())).all()


@router.post("/deploys/", response_model=DeployRead, status_code=201)
def create_deploy(payload: DeployCreate, session: Session = Depends(get_session)):
    if not session.get(Service, payload.service_id):
        raise HTTPException(404, "Service not found.")
    deploy = Deploy(**payload.model_dump())
    session.add(deploy)
    session.commit()
    session.refresh(deploy)
    return deploy


@router.get("/incidents/", response_model=list[PastIncidentRead])
def list_incidents(session: Session = Depends(get_session)):
    return session.exec(select(PastIncident).order_by(PastIncident.resolved_at.desc())).all()


@router.post("/incidents/", response_model=PastIncidentRead, status_code=201)
def create_incident(payload: PastIncidentCreate, session: Session = Depends(get_session)):
    if not session.get(Service, payload.service_id):
        raise HTTPException(404, "Service not found.")
    incident = PastIncident(**payload.model_dump())
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident
