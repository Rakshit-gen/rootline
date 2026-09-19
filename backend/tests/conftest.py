import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401 - ensure tables are registered on metadata


@pytest.fixture()
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
