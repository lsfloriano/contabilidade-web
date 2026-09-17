import pytest
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db import get_engine, get_sessionmaker, init_db, get_db
from app.seed import seed_plano_de_contas
from app.main import app


@pytest.fixture()
def db_session():
    engine = get_engine("sqlite:///:memory:", poolclass=StaticPool)
    init_db(engine)
    Session = get_sessionmaker(engine)
    session = Session()
    seed_plano_de_contas(session)
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
