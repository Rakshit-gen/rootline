from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    owner_team: str
    depends_on: str = Field(default="", description="comma-separated service names this service calls")


class Deploy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id", index=True)
    commit_sha: str
    description: str
    deployed_at: datetime


class PastIncident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id", index=True)
    signature: str = Field(description="short symptom description, e.g. '5xx spike on checkout'")
    root_cause: str
    resolved_at: datetime


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id", index=True)
    title: str
    description: str
    status: str = Field(default="open")  # open | investigating | resolved
    fired_at: datetime


class AgentRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alert_id: int = Field(foreign_key="alert.id", index=True)
    status: str = Field(default="running")  # running | completed
    hypotheses: list = Field(default_factory=list, sa_column=Column(JSON))
    confirmed_hypothesis: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None


class AgentStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="agentrun.id", index=True)
    step_number: int
    thought: str
    tool_name: str = Field(default="")
    tool_args: dict = Field(default_factory=dict, sa_column=Column(JSON))
    observation: dict = Field(default_factory=dict, sa_column=Column(JSON))
