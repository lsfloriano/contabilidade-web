import asyncio

from app.db import get_engine, get_sessionmaker
from app.main import app, lifespan
from app.models import ContaContabil


def test_lifespan_inicializa_e_semeia_banco(tmp_path, monkeypatch):
    db_path = tmp_path / "boot_test.db"
    test_engine = get_engine(f"sqlite:///{db_path}")
    test_sessionmaker = get_sessionmaker(test_engine)

    monkeypatch.setattr("app.main.engine", test_engine)
    monkeypatch.setattr("app.main.SessionLocal", test_sessionmaker)

    async def executar_lifespan():
        async with lifespan(app):
            pass

    asyncio.run(executar_lifespan())

    db = test_sessionmaker()
    try:
        assert db.query(ContaContabil).count() == 20
    finally:
        db.close()
