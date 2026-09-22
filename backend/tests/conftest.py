import pytest
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.auth import criar_token
from app.db import get_engine, get_sessionmaker, init_db, get_db
from app.seed import seed_plano_de_contas, seed_usuarios
from app.main import app


@pytest.fixture()
def db_session():
    engine = get_engine("sqlite:///:memory:", poolclass=StaticPool)
    init_db(engine)
    Session = get_sessionmaker(engine)
    session = Session()
    seed_plano_de_contas(session)
    seed_usuarios(session)
    yield session
    session.close()


# Só o override de banco, sem cliente: os três fixtures de cliente abaixo
# nascem daqui, cada um com o seu próprio TestClient, para um teste poder
# pedir dois clientes diferentes sem que um sobrescreva o header do outro.
@pytest.fixture()
def app_com_db(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


# O cliente padrão de todos os testes do projeto: já autenticado, com token
# de conta comum. Toda rota protegida exige header Authorization, e repetir
# isso em cada uma das dezenas de chamadas existentes não provaria nada além
# do que test_auth_api.py já prova. Testes de ausência/invalidez de token
# usam client_sem_token, explicitamente.
@pytest.fixture()
def client(app_com_db):
    token = criar_token("teste1@contabilidade.com")
    return TestClient(app_com_db, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture()
def client_admin(app_com_db):
    token = criar_token("admin@contabilidade.com")
    return TestClient(app_com_db, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture()
def client_sem_token(app_com_db):
    return TestClient(app_com_db)
