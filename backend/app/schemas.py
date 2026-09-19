from datetime import datetime

from pydantic import BaseModel


class ServiceRead(BaseModel):
    id: int
    name: str
    owner_team: str
    depends_on: str


class ServiceCreate(BaseModel):
    name: str
    owner_team: str
    depends_on: str = ""


class DeployRead(BaseModel):
    id: int
    service_id: int
    commit_sha: str
    description: str
    deployed_at: datetime


class DeployCreate(BaseModel):
    service_id: int
    commit_sha: str
    description: str
    deployed_at: datetime


class PastIncidentRead(BaseModel):
    id: int
    service_id: int
    signature: str
    root_cause: str
    resolved_at: datetime


class PastIncidentCreate(BaseModel):
    service_id: int
    signature: str
    root_cause: str
    resolved_at: datetime


class AlertRead(BaseModel):
    id: int
    service_id: int
    title: str
    description: str
    status: str
    fired_at: datetime


class AlertCreate(BaseModel):
    service_id: int
    title: str
    description: str
    fired_at: datetime


class AgentStepRead(BaseModel):
    id: int
    step_number: int
    thought: str
    tool_name: str
    tool_args: dict
    observation: dict


class AgentRunRead(BaseModel):
    id: int
    alert_id: int
    status: str
    hypotheses: list
    confirmed_hypothesis: str | None
    started_at: datetime
    decided_at: datetime | None
    steps: list[AgentStepRead] = []


class ConfirmHypothesis(BaseModel):
    cause: str
