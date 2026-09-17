# Contabilidade Web Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web app that replicates the basic accounting cycle (journal entries → ledger/trial balance → Balance Sheet and Income Statement) using FastAPI + pandas on the backend and React on the frontend.

**Architecture:** FastAPI backend backed by SQLite (via SQLAlchemy) exposes a JSON API; pandas reads journal entries + chart of accounts into DataFrames on every report request and computes trial balance / Balance Sheet / Income Statement on the fly (no caching). A React (Vite) SPA consumes the API.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, pandas, pytest, httpx; React 18 + Vite (no CSS framework).

**Spec:** `docs/superpowers/specs/2026-09-17-contabilidade-web-design.md`

## Global Constraints

- Partida dobrada simples: cada lançamento tem exatamente 1 conta debitada e 1 creditada — sem lançamentos compostos.
- Plano de contas fixo e pré-definido — sem customização pelo usuário nesta versão.
- Período único contínuo — sem fechamento de exercício/zeramento de contas de resultado.
- Aplicação single-user, local — sem autenticação.
- Sem testes automatizados de frontend nesta versão — verificação manual no navegador.
- CORS liberado apenas para `http://localhost:5173` (dev server do Vite).

---

## Task 1: Database models, engine helpers, and seed data

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/app/__init__.py`
- Create: `backend/app/models.py`
- Create: `backend/app/db.py`
- Create: `backend/app/seed.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_seed.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `Base` (declarative base, `app.models`), `ContaContabil` and `Lancamento` ORM models (`app.models`), `Natureza`/`Grupo`/`TipoConta` enums (`app.models`), `get_engine(database_url=..., **kwargs)`, `get_sessionmaker(engine)`, `init_db(engine)`, `engine`, `get_db()` (`app.db`), `seed_plano_de_contas(db)` (`app.seed`).

- [ ] **Step 1: Create `.gitignore`**

```gitignore
__pycache__/
*.pyc
backend/contabilidade.db
.venv/
venv/
node_modules/
dist/
.DS_Store
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pandas==2.2.3
pydantic==2.9.2
pytest==8.3.3
httpx==0.27.2
python-multipart==0.0.9
```

- [ ] **Step 3: Create `backend/pytest.ini`**

```ini
[pytest]
pythonpath = .
```

- [ ] **Step 4: Create `backend/app/__init__.py`** (empty file)

- [ ] **Step 5: Create `backend/tests/__init__.py`** (empty file)

- [ ] **Step 6: Set up a virtualenv and install dependencies**

Run: `cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt` (Windows) or `source .venv/bin/activate && pip install -r requirements.txt` (POSIX)

- [ ] **Step 7: Write the failing test for the seed**

`backend/tests/test_seed.py`:

```python
from app.db import get_engine, get_sessionmaker, init_db
from app.seed import seed_plano_de_contas
from app.models import ContaContabil


def test_seed_cria_plano_de_contas_padrao():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = get_sessionmaker(engine)
    db = Session()

    seed_plano_de_contas(db)

    contas = db.query(ContaContabil).all()
    assert len(contas) == 20

    caixa = db.query(ContaContabil).filter_by(codigo="1.1.01").first()
    assert caixa.nome == "Caixa"
    assert caixa.natureza.value == "devedora"
    assert caixa.grupo.value == "Ativo Circulante"
    assert caixa.tipo.value == "patrimonial"

    db.close()


def test_seed_e_idempotente():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = get_sessionmaker(engine)
    db = Session()

    seed_plano_de_contas(db)
    seed_plano_de_contas(db)

    assert db.query(ContaContabil).count() == 20
    db.close()
```

- [ ] **Step 8: Run the test to verify it fails**

Run: `cd backend && pytest tests/test_seed.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.models'` or similar — nothing exists yet)

- [ ] **Step 9: Create `backend/app/models.py`**

```python
import enum

from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Natureza(str, enum.Enum):
    devedora = "devedora"
    credora = "credora"


class Grupo(str, enum.Enum):
    ativo_circulante = "Ativo Circulante"
    ativo_nao_circulante = "Ativo Não Circulante"
    passivo_circulante = "Passivo Circulante"
    passivo_nao_circulante = "Passivo Não Circulante"
    patrimonio_liquido = "Patrimônio Líquido"
    receita = "Receita"
    despesa = "Despesa"


class TipoConta(str, enum.Enum):
    patrimonial = "patrimonial"
    resultado = "resultado"


class ContaContabil(Base):
    __tablename__ = "plano_de_contas"

    codigo = Column(String, primary_key=True)
    nome = Column(String, nullable=False)
    natureza = Column(Enum(Natureza), nullable=False)
    grupo = Column(Enum(Grupo), nullable=False)
    tipo = Column(Enum(TipoConta), nullable=False)


class Lancamento(Base):
    __tablename__ = "lancamentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
    conta_debito = Column(String, ForeignKey("plano_de_contas.codigo"), nullable=False)
    conta_credito = Column(String, ForeignKey("plano_de_contas.codigo"), nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    historico = Column(String, nullable=True)

    debito = relationship("ContaContabil", foreign_keys=[conta_debito])
    credito = relationship("ContaContabil", foreign_keys=[conta_credito])
```

- [ ] **Step 10: Create `backend/app/db.py`**

```python
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./contabilidade.db")


def get_engine(database_url: str = DATABASE_URL, **kwargs):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, **kwargs)


def get_sessionmaker(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine):
    Base.metadata.create_all(bind=engine)


engine = get_engine()
SessionLocal = get_sessionmaker(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 11: Create `backend/app/seed.py`**

```python
from app.models import ContaContabil, Natureza, Grupo, TipoConta

PLANO_DE_CONTAS_PADRAO = [
    # Ativo Circulante
    {"codigo": "1.1.01", "nome": "Caixa", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.1.02", "nome": "Bancos", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.1.03", "nome": "Clientes", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.1.04", "nome": "Estoques", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    # Ativo Não Circulante
    {"codigo": "1.2.01", "nome": "Imobilizado", "natureza": Natureza.devedora, "grupo": Grupo.ativo_nao_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.2.02", "nome": "Investimentos", "natureza": Natureza.devedora, "grupo": Grupo.ativo_nao_circulante, "tipo": TipoConta.patrimonial},
    # Passivo Circulante
    {"codigo": "2.1.01", "nome": "Fornecedores", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "2.1.02", "nome": "Empréstimos CP", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "2.1.03", "nome": "Salários a Pagar", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "2.1.04", "nome": "Impostos a Pagar", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    # Passivo Não Circulante
    {"codigo": "2.2.01", "nome": "Empréstimos LP", "natureza": Natureza.credora, "grupo": Grupo.passivo_nao_circulante, "tipo": TipoConta.patrimonial},
    # Patrimônio Líquido
    {"codigo": "2.3.01", "nome": "Capital Social", "natureza": Natureza.credora, "grupo": Grupo.patrimonio_liquido, "tipo": TipoConta.patrimonial},
    {"codigo": "2.3.02", "nome": "Lucros/Prejuízos Acumulados", "natureza": Natureza.credora, "grupo": Grupo.patrimonio_liquido, "tipo": TipoConta.patrimonial},
    # Receita
    {"codigo": "3.1.01", "nome": "Receita de Vendas", "natureza": Natureza.credora, "grupo": Grupo.receita, "tipo": TipoConta.resultado},
    {"codigo": "3.1.02", "nome": "Receita de Serviços", "natureza": Natureza.credora, "grupo": Grupo.receita, "tipo": TipoConta.resultado},
    # Despesa
    {"codigo": "4.1.01", "nome": "CMV", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.02", "nome": "Despesas Administrativas", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.03", "nome": "Despesas com Vendas", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.04", "nome": "Despesas Financeiras", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.05", "nome": "Impostos sobre Vendas", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
]


def seed_plano_de_contas(db):
    if db.query(ContaContabil).count() > 0:
        return
    for conta in PLANO_DE_CONTAS_PADRAO:
        db.add(ContaContabil(**conta))
    db.commit()
```

- [ ] **Step 12: Run the test to verify it passes**

Run: `cd backend && pytest tests/test_seed.py -v`
Expected: PASS (2 tests)

- [ ] **Step 13: Commit**

```bash
git add .gitignore backend/requirements.txt backend/pytest.ini backend/app backend/tests
git commit -m "feat: add accounting models, db helpers, and chart of accounts seed"
```

---

## Task 2: FastAPI app skeleton + GET /contas endpoint

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/contas.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_contas_api.py`

**Interfaces:**
- Consumes: `engine`, `get_db`, `SessionLocal` (`app.db`), `seed_plano_de_contas` (`app.seed`), `ContaContabil` (`app.models`)
- Produces: `app` (FastAPI instance, `app.main`), `ContaOut` schema (`app.schemas`), `contas.router` (`app.routers.contas`), pytest fixtures `db_session` and `client` (`tests/conftest.py`) — used by every subsequent backend test file.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_contas_api.py`:

```python
def test_listar_contas_retorna_plano_padrao(client):
    resposta = client.get("/contas")
    assert resposta.status_code == 200

    contas = resposta.json()
    assert len(contas) == 20

    caixa = next(c for c in contas if c["codigo"] == "1.1.01")
    assert caixa["nome"] == "Caixa"
    assert caixa["natureza"] == "devedora"
    assert caixa["grupo"] == "Ativo Circulante"
    assert caixa["tipo"] == "patrimonial"
```

Note: this test depends on the `client` fixture defined in Step 2 below — write both files before running.

- [ ] **Step 2: Create `backend/tests/conftest.py`**

```python
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
```

- [ ] **Step 3: Create `backend/app/schemas.py`**

```python
from pydantic import BaseModel, ConfigDict


class ContaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str
    natureza: str
    grupo: str
    tipo: str
```

- [ ] **Step 4: Create `backend/app/routers/__init__.py`** (empty file)

- [ ] **Step 5: Create `backend/app/routers/contas.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ContaContabil
from app.schemas import ContaOut

router = APIRouter()


@router.get("/contas", response_model=list[ContaOut])
def listar_contas(db: Session = Depends(get_db)):
    return db.query(ContaContabil).order_by(ContaContabil.codigo).all()
```

- [ ] **Step 6: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, init_db, SessionLocal
from app.seed import seed_plano_de_contas
from app.routers import contas

app = FastAPI(title="Contabilidade Web")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db(engine)
    db = SessionLocal()
    try:
        seed_plano_de_contas(db)
    finally:
        db.close()


@app.get("/")
def health():
    return {"status": "ok"}


app.include_router(contas.router)
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `cd backend && pytest tests/test_contas_api.py -v`
Expected: PASS (1 test). This will create/seed a real `backend/contabilidade.db` file as a side effect of the app's startup event — this is expected and gitignored.

- [ ] **Step 8: Commit**

```bash
git add backend/app/main.py backend/app/schemas.py backend/app/routers backend/tests/conftest.py backend/tests/test_contas_api.py
git commit -m "feat: add FastAPI app skeleton and GET /contas endpoint"
```

---

## Task 3: POST /lancamentos + GET /lancamentos with validation

**Files:**
- Create: `backend/app/validacao.py`
- Modify: `backend/app/schemas.py` (add `LancamentoCreate`, `LancamentoOut`)
- Create: `backend/app/routers/lancamentos.py`
- Modify: `backend/app/main.py` (include `lancamentos.router`)
- Create: `backend/tests/test_lancamentos_api.py`

**Interfaces:**
- Consumes: `get_db` (`app.db`), `ContaContabil`, `Lancamento` (`app.models`), `client`/`db_session` fixtures (`tests/conftest.py`)
- Produces: `validar_lancamento(db, conta_debito, conta_credito, valor)` and `LancamentoInvalido` exception (`app.validacao`) — reused by CSV upload in Task 7. `lancamentos.router` (`app.routers.lancamentos`).

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_lancamentos_api.py`:

```python
def test_criar_lancamento_valido(client):
    resposta = client.post(
        "/lancamentos",
        json={
            "data": "2026-01-05",
            "conta_debito": "1.1.01",
            "conta_credito": "2.3.01",
            "valor": 1000.0,
            "historico": "Integralização de capital",
        },
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] is not None
    assert corpo["conta_debito"] == "1.1.01"
    assert corpo["conta_credito"] == "2.3.01"


def test_criar_lancamento_conta_inexistente(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "9.9.99", "conta_credito": "2.3.01", "valor": 100.0},
    )
    assert resposta.status_code == 422


def test_criar_lancamento_debito_igual_credito(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "1.1.01", "valor": 100.0},
    )
    assert resposta.status_code == 422


def test_criar_lancamento_valor_invalido(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 0},
    )
    assert resposta.status_code == 422


def test_listar_lancamentos_ordenado_por_data(client):
    client.post("/lancamentos", json={"data": "2026-01-10", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 50.0})
    client.post("/lancamentos", json={"data": "2026-01-02", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 20.0})

    resposta = client.get("/lancamentos")
    corpo = resposta.json()
    assert [l["data"] for l in corpo] == ["2026-01-02", "2026-01-10"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && pytest tests/test_lancamentos_api.py -v`
Expected: FAIL (404 — no `/lancamentos` route yet)

- [ ] **Step 3: Create `backend/app/validacao.py`**

```python
from sqlalchemy.orm import Session

from app.models import ContaContabil


class LancamentoInvalido(ValueError):
    pass


def validar_lancamento(db: Session, conta_debito: str, conta_credito: str, valor: float) -> None:
    if valor is None or valor <= 0:
        raise LancamentoInvalido("valor deve ser maior que zero")

    if conta_debito == conta_credito:
        raise LancamentoInvalido("conta_debito e conta_credito devem ser diferentes")

    if db.query(ContaContabil).filter_by(codigo=conta_debito).first() is None:
        raise LancamentoInvalido(f"conta_debito '{conta_debito}' não existe no plano de contas")

    if db.query(ContaContabil).filter_by(codigo=conta_credito).first() is None:
        raise LancamentoInvalido(f"conta_credito '{conta_credito}' não existe no plano de contas")
```

- [ ] **Step 4: Add to `backend/app/schemas.py`**

Append:

```python
from datetime import date
from typing import Optional


class LancamentoCreate(BaseModel):
    data: date
    conta_debito: str
    conta_credito: str
    valor: float
    historico: Optional[str] = None


class LancamentoOut(LancamentoCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
```

- [ ] **Step 5: Create `backend/app/routers/lancamentos.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Lancamento
from app.schemas import LancamentoCreate, LancamentoOut
from app.validacao import validar_lancamento, LancamentoInvalido

router = APIRouter()


@router.post("/lancamentos", response_model=LancamentoOut, status_code=201)
def criar_lancamento(payload: LancamentoCreate, db: Session = Depends(get_db)):
    try:
        validar_lancamento(db, payload.conta_debito, payload.conta_credito, payload.valor)
    except LancamentoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    lancamento = Lancamento(**payload.model_dump())
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.get("/lancamentos", response_model=list[LancamentoOut])
def listar_lancamentos(db: Session = Depends(get_db)):
    return db.query(Lancamento).order_by(Lancamento.data).all()
```

- [ ] **Step 6: Modify `backend/app/main.py`**

Add the import alongside the existing `from app.routers import contas` line:

```python
from app.routers import contas, lancamentos
```

Add after `app.include_router(contas.router)`:

```python
app.include_router(lancamentos.router)
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd backend && pytest tests/test_lancamentos_api.py -v`
Expected: PASS (5 tests)

- [ ] **Step 8: Commit**

```bash
git add backend/app/validacao.py backend/app/schemas.py backend/app/routers/lancamentos.py backend/app/main.py backend/tests/test_lancamentos_api.py
git commit -m "feat: add lancamentos CRUD with double-entry validation"
```

---

## Task 4: Trial balance (balancete) calculation + GET /relatorios/balancete

**Files:**
- Create: `backend/app/relatorios.py`
- Modify: `backend/app/schemas.py` (add `BalanceteRow`)
- Create: `backend/app/routers/relatorios.py`
- Modify: `backend/app/main.py` (include `relatorios.router`)
- Create: `backend/tests/test_relatorios_balancete.py`

**Interfaces:**
- Consumes: `Lancamento`, `ContaContabil`, `Natureza` (`app.models`)
- Produces: `calcular_balancete(db) -> list[dict]` (`app.relatorios`) — each dict has keys `codigo, nome, grupo, tipo, total_debito, total_credito, saldo`. Reused by Tasks 5 and 6. `relatorios.router` (`app.routers.relatorios`), mounted at prefix `/relatorios`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_relatorios_balancete.py`:

```python
from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import calcular_balancete


def test_calcular_balancete_soma_debitos_e_creditos(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 10), conta_debito="1.1.04", conta_credito="1.1.01", valor=Decimal("300.00"), historico="Compra de estoque à vista"),
    ])
    db_session.commit()

    balancete = calcular_balancete(db_session)

    caixa = next(c for c in balancete if c["codigo"] == "1.1.01")
    assert caixa["total_debito"] == 1000.00
    assert caixa["total_credito"] == 300.00
    assert caixa["saldo"] == 700.00  # devedora: debito - credito

    capital = next(c for c in balancete if c["codigo"] == "2.3.01")
    assert capital["saldo"] == 1000.00  # credora: credito - debito

    estoques = next(c for c in balancete if c["codigo"] == "1.1.04")
    assert estoques["saldo"] == 300.00


def test_calcular_balancete_sem_lancamentos_retorna_zerado(db_session):
    balancete = calcular_balancete(db_session)
    assert len(balancete) == 20
    assert all(c["saldo"] == 0.0 for c in balancete)


def test_endpoint_balancete(client, db_session):
    db_session.add(Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00")))
    db_session.commit()

    resposta = client.get("/relatorios/balancete")
    assert resposta.status_code == 200
    linhas = resposta.json()
    caixa = next(l for l in linhas if l["codigo"] == "1.1.01")
    assert caixa["saldo"] == 1000.00
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && pytest tests/test_relatorios_balancete.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.relatorios'`)

- [ ] **Step 3: Create `backend/app/relatorios.py`**

```python
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Lancamento, ContaContabil, Natureza


def _lancamentos_dataframe(db: Session) -> pd.DataFrame:
    lancamentos = db.query(Lancamento).all()
    rows = [
        {"conta_debito": l.conta_debito, "conta_credito": l.conta_credito, "valor": float(l.valor)}
        for l in lancamentos
    ]
    return pd.DataFrame(rows, columns=["conta_debito", "conta_credito", "valor"])


def _contas_dataframe(db: Session) -> pd.DataFrame:
    contas = db.query(ContaContabil).all()
    return pd.DataFrame([
        {
            "codigo": c.codigo,
            "nome": c.nome,
            "natureza": c.natureza.value,
            "grupo": c.grupo.value,
            "tipo": c.tipo.value,
        }
        for c in contas
    ])


def calcular_balancete(db: Session) -> list[dict]:
    lanc_df = _lancamentos_dataframe(db)
    contas_df = _contas_dataframe(db)

    if lanc_df.empty:
        debitos = pd.Series(dtype=float)
        creditos = pd.Series(dtype=float)
    else:
        debitos = lanc_df.groupby("conta_debito")["valor"].sum()
        creditos = lanc_df.groupby("conta_credito")["valor"].sum()

    resultado = []
    for _, conta in contas_df.iterrows():
        total_debito = float(debitos.get(conta["codigo"], 0.0))
        total_credito = float(creditos.get(conta["codigo"], 0.0))

        if conta["natureza"] == Natureza.devedora.value:
            saldo = total_debito - total_credito
        else:
            saldo = total_credito - total_debito

        resultado.append({
            "codigo": conta["codigo"],
            "nome": conta["nome"],
            "grupo": conta["grupo"],
            "tipo": conta["tipo"],
            "total_debito": total_debito,
            "total_credito": total_credito,
            "saldo": saldo,
        })
    return resultado
```

- [ ] **Step 4: Add to `backend/app/schemas.py`**

Append:

```python
class BalanceteRow(BaseModel):
    codigo: str
    nome: str
    grupo: str
    tipo: str
    total_debito: float
    total_credito: float
    saldo: float
```

- [ ] **Step 5: Create `backend/app/routers/relatorios.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.relatorios import calcular_balancete
from app.schemas import BalanceteRow

router = APIRouter(prefix="/relatorios")


@router.get("/balancete", response_model=list[BalanceteRow])
def obter_balancete(db: Session = Depends(get_db)):
    return calcular_balancete(db)
```

- [ ] **Step 6: Modify `backend/app/main.py`**

Change the routers import line to:

```python
from app.routers import contas, lancamentos, relatorios
```

Add after `app.include_router(lancamentos.router)`:

```python
app.include_router(relatorios.router)
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd backend && pytest tests/test_relatorios_balancete.py -v`
Expected: PASS (3 tests)

- [ ] **Step 8: Commit**

```bash
git add backend/app/relatorios.py backend/app/schemas.py backend/app/routers/relatorios.py backend/app/main.py backend/tests/test_relatorios_balancete.py
git commit -m "feat: compute trial balance with pandas and expose /relatorios/balancete"
```

---

## Task 5: Balanço Patrimonial (BP) calculation + GET /relatorios/bp

**Files:**
- Modify: `backend/app/relatorios.py` (add `montar_bp`)
- Modify: `backend/app/schemas.py` (add `BPConta`, `BPSecao`, `BPReport`)
- Modify: `backend/app/routers/relatorios.py` (add `/bp` route)
- Create: `backend/tests/test_relatorios_bp.py`

**Interfaces:**
- Consumes: `calcular_balancete(db)` (`app.relatorios`, from Task 4)
- Produces: `montar_bp(db) -> dict` (`app.relatorios`) with keys `ativo, passivo_pl, total_ativo, total_passivo_pl, balanceado`; each section is `{grupo, contas: [{codigo, nome, saldo}], subtotal}`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_relatorios_bp.py`:

```python
from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import montar_bp


def test_montar_bp_bate_ativo_com_passivo_mais_pl(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.04", conta_credito="2.1.01", valor=Decimal("2000.00"), historico="Compra de estoque a prazo"),
        Lancamento(data=date(2026, 1, 10), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("1000.00"), historico="Compra de imobilizado à vista"),
    ])
    db_session.commit()

    bp = montar_bp(db_session)

    assert bp["total_ativo"] == 7000.00
    assert bp["total_passivo_pl"] == 7000.00
    assert bp["balanceado"] is True

    ativo_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Circulante")
    assert ativo_circulante["subtotal"] == 6000.00

    ativo_nao_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Não Circulante")
    assert ativo_nao_circulante["subtotal"] == 1000.00

    patrimonio_liquido = next(s for s in bp["passivo_pl"] if s["grupo"] == "Patrimônio Líquido")
    assert patrimonio_liquido["subtotal"] == 5000.00


def test_endpoint_bp(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-02", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 500.0},
    )
    assert resposta.status_code == 201

    resposta = client.get("/relatorios/bp")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["balanceado"] is True
    assert corpo["total_ativo"] == 500.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && pytest tests/test_relatorios_bp.py -v`
Expected: FAIL (`ImportError: cannot import name 'montar_bp'`)

- [ ] **Step 3: Add to `backend/app/relatorios.py`**

Append:

```python
GRUPOS_ATIVO = ["Ativo Circulante", "Ativo Não Circulante"]
GRUPOS_PASSIVO_PL = ["Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido"]


def _agrupar_secoes(contas: list[dict], grupos: list[str]) -> tuple[list[dict], float]:
    secoes = []
    total = 0.0
    for grupo in grupos:
        contas_grupo = [c for c in contas if c["grupo"] == grupo]
        subtotal = sum(c["saldo"] for c in contas_grupo)
        total += subtotal
        secoes.append({
            "grupo": grupo,
            "contas": [{"codigo": c["codigo"], "nome": c["nome"], "saldo": c["saldo"]} for c in contas_grupo],
            "subtotal": subtotal,
        })
    return secoes, total


def montar_bp(db: Session) -> dict:
    balancete = calcular_balancete(db)
    patrimoniais = [c for c in balancete if c["tipo"] == "patrimonial"]

    ativo_secoes, total_ativo = _agrupar_secoes(patrimoniais, GRUPOS_ATIVO)
    passivo_pl_secoes, total_passivo_pl = _agrupar_secoes(patrimoniais, GRUPOS_PASSIVO_PL)

    return {
        "ativo": ativo_secoes,
        "passivo_pl": passivo_pl_secoes,
        "total_ativo": total_ativo,
        "total_passivo_pl": total_passivo_pl,
        "balanceado": abs(total_ativo - total_passivo_pl) < 0.01,
    }
```

- [ ] **Step 4: Add to `backend/app/schemas.py`**

Append:

```python
class BPConta(BaseModel):
    codigo: str
    nome: str
    saldo: float


class BPSecao(BaseModel):
    grupo: str
    contas: list[BPConta]
    subtotal: float


class BPReport(BaseModel):
    ativo: list[BPSecao]
    passivo_pl: list[BPSecao]
    total_ativo: float
    total_passivo_pl: float
    balanceado: bool
```

- [ ] **Step 5: Add to `backend/app/routers/relatorios.py`**

Update the import line:

```python
from app.relatorios import calcular_balancete, montar_bp
from app.schemas import BalanceteRow, BPReport
```

Append:

```python
@router.get("/bp", response_model=BPReport)
def obter_bp(db: Session = Depends(get_db)):
    return montar_bp(db)
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd backend && pytest tests/test_relatorios_bp.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/relatorios.py backend/app/schemas.py backend/app/routers/relatorios.py backend/tests/test_relatorios_bp.py
git commit -m "feat: build Balance Sheet report and expose /relatorios/bp"
```

---

## Task 6: DRE (Income Statement) calculation + GET /relatorios/dre

**Files:**
- Modify: `backend/app/relatorios.py` (add `montar_dre`)
- Modify: `backend/app/schemas.py` (add `DREConta`, `DREReport`)
- Modify: `backend/app/routers/relatorios.py` (add `/dre` route)
- Create: `backend/tests/test_relatorios_dre.py`

**Interfaces:**
- Consumes: `calcular_balancete(db)` (`app.relatorios`, from Task 4)
- Produces: `montar_dre(db) -> dict` (`app.relatorios`) with keys `receitas, despesas, total_receitas, total_despesas, resultado_periodo`; `receitas`/`despesas` are lists of `{codigo, nome, valor}`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_relatorios_dre.py`:

```python
from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import montar_dre


def test_montar_dre_calcula_resultado(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 3), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00"), historico="Venda a prazo"),
        Lancamento(data=date(2026, 1, 3), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00"), historico="Baixa de CMV"),
    ])
    db_session.commit()

    dre = montar_dre(db_session)

    assert dre["total_receitas"] == 3000.00
    assert dre["total_despesas"] == 1200.00
    assert dre["resultado_periodo"] == 1800.00

    receita_vendas = next(c for c in dre["receitas"] if c["codigo"] == "3.1.01")
    assert receita_vendas["valor"] == 3000.00


def test_endpoint_dre(client):
    client.post("/lancamentos", json={"data": "2026-01-03", "conta_debito": "1.1.03", "conta_credito": "3.1.01", "valor": 500.0})

    resposta = client.get("/relatorios/dre")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resultado_periodo"] == 500.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && pytest tests/test_relatorios_dre.py -v`
Expected: FAIL (`ImportError: cannot import name 'montar_dre'`)

- [ ] **Step 3: Add to `backend/app/relatorios.py`**

Append:

```python
def montar_dre(db: Session) -> dict:
    balancete = calcular_balancete(db)
    resultado_contas = [c for c in balancete if c["tipo"] == "resultado"]

    receitas = [c for c in resultado_contas if c["grupo"] == "Receita"]
    despesas = [c for c in resultado_contas if c["grupo"] == "Despesa"]

    total_receitas = sum(c["saldo"] for c in receitas)
    total_despesas = sum(c["saldo"] for c in despesas)

    return {
        "receitas": [{"codigo": c["codigo"], "nome": c["nome"], "valor": c["saldo"]} for c in receitas],
        "despesas": [{"codigo": c["codigo"], "nome": c["nome"], "valor": c["saldo"]} for c in despesas],
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_periodo": total_receitas - total_despesas,
    }
```

- [ ] **Step 4: Add to `backend/app/schemas.py`**

Append:

```python
class DREConta(BaseModel):
    codigo: str
    nome: str
    valor: float


class DREReport(BaseModel):
    receitas: list[DREConta]
    despesas: list[DREConta]
    total_receitas: float
    total_despesas: float
    resultado_periodo: float
```

- [ ] **Step 5: Add to `backend/app/routers/relatorios.py`**

Update the import lines:

```python
from app.relatorios import calcular_balancete, montar_bp, montar_dre
from app.schemas import BalanceteRow, BPReport, DREReport
```

Append:

```python
@router.get("/dre", response_model=DREReport)
def obter_dre(db: Session = Depends(get_db)):
    return montar_dre(db)
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd backend && pytest tests/test_relatorios_dre.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/relatorios.py backend/app/schemas.py backend/app/routers/relatorios.py backend/tests/test_relatorios_dre.py
git commit -m "feat: build Income Statement report and expose /relatorios/dre"
```

---

## Task 7: CSV batch upload for lançamentos

**Files:**
- Modify: `backend/app/routers/lancamentos.py` (add `/lancamentos/upload` route)
- Modify: `backend/app/schemas.py` (add `UploadErro`, `UploadResultado`)
- Create: `backend/tests/test_upload_csv.py`

**Interfaces:**
- Consumes: `validar_lancamento`, `LancamentoInvalido` (`app.validacao`, from Task 3), `Lancamento` (`app.models`)
- Produces: `POST /lancamentos/upload` returning `UploadResultado {inseridos: int, erros: [{linha: int, motivo: str}]}`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_upload_csv.py`:

```python
CSV_CONTEUDO = (
    "data,conta_debito,conta_credito,valor,historico\n"
    "2026-01-02,1.1.01,2.3.01,5000,Integralizacao de capital\n"
    "2026-01-05,9.9.99,2.1.01,2000,Conta inexistente\n"
    "2026-01-06,1.1.04,2.1.01,-100,Valor negativo\n"
)


def test_upload_csv_insere_validos_e_reporta_invalidos(client):
    resposta = client.post(
        "/lancamentos/upload",
        files={"arquivo": ("lancamentos.csv", CSV_CONTEUDO, "text/csv")},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["inseridos"] == 1
    assert len(corpo["erros"]) == 2
    assert corpo["erros"][0]["linha"] == 3
    assert corpo["erros"][1]["linha"] == 4

    lancamentos = client.get("/lancamentos").json()
    assert len(lancamentos) == 1
    assert lancamentos[0]["conta_debito"] == "1.1.01"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && pytest tests/test_upload_csv.py -v`
Expected: FAIL (404 — no `/lancamentos/upload` route yet)

- [ ] **Step 3: Add to `backend/app/schemas.py`**

Append:

```python
class UploadErro(BaseModel):
    linha: int
    motivo: str


class UploadResultado(BaseModel):
    inseridos: int
    erros: list[UploadErro]
```

- [ ] **Step 4: Add to `backend/app/routers/lancamentos.py`**

Update the imports at the top of the file:

```python
import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Lancamento
from app.schemas import LancamentoCreate, LancamentoOut, UploadErro, UploadResultado
from app.validacao import validar_lancamento, LancamentoInvalido
```

Append:

```python
@router.post("/lancamentos/upload", response_model=UploadResultado)
async def upload_lancamentos(db: Session = Depends(get_db), arquivo: UploadFile = File(...)):
    conteudo = await arquivo.read()
    df = pd.read_csv(io.BytesIO(conteudo))

    inseridos = 0
    erros: list[UploadErro] = []

    for indice, linha in df.iterrows():
        numero_linha = indice + 2  # +1 for header row, +1 to make it 1-indexed

        try:
            conta_debito = str(linha["conta_debito"]).strip()
            conta_credito = str(linha["conta_credito"]).strip()
            valor = float(linha["valor"])
            validar_lancamento(db, conta_debito, conta_credito, valor)
        except (LancamentoInvalido, KeyError, ValueError) as exc:
            erros.append(UploadErro(linha=numero_linha, motivo=str(exc)))
            continue

        historico = linha.get("historico")
        db.add(Lancamento(
            data=pd.to_datetime(linha["data"]).date(),
            conta_debito=conta_debito,
            conta_credito=conta_credito,
            valor=valor,
            historico=None if pd.isna(historico) else historico,
        ))
        inseridos += 1

    db.commit()
    return UploadResultado(inseridos=inseridos, erros=erros)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd backend && pytest tests/test_upload_csv.py -v`
Expected: PASS (1 test)

- [ ] **Step 6: Run the full backend test suite**

Run: `cd backend && pytest -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/lancamentos.py backend/app/schemas.py backend/tests/test_upload_csv.py
git commit -m "feat: add CSV batch upload for lancamentos"
```

---

## Task 8: Frontend scaffold, navigation, and API client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/api.js`
- Create: `frontend/src/index.css`
- Create: `frontend/src/pages/Lancamentos.jsx` (placeholder)
- Create: `frontend/src/pages/Balancete.jsx` (placeholder)
- Create: `frontend/src/pages/BalancoPatrimonial.jsx` (placeholder)
- Create: `frontend/src/pages/DRE.jsx` (placeholder)

**Interfaces:**
- Produces: `getContas`, `getLancamentos`, `criarLancamento`, `uploadLancamentos`, `getBalancete`, `getBP`, `getDRE` (`frontend/src/api.js`) — all return the parsed JSON body as a Promise, or reject with an `Error` whose `.message` is the API's error detail. `App` component with tab navigation (`frontend/src/App.jsx`).

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "contabilidade-web-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Create `frontend/vite.config.js`**

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
```

- [ ] **Step 3: Create `frontend/index.html`**

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <title>Contabilidade Web</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Create `frontend/src/api.js`**

```javascript
const API_BASE = "http://localhost:8000";

async function handleResponse(resposta) {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    throw new Error(corpo.detail || `Erro ${resposta.status}`);
  }
  return resposta.json();
}

export function getContas() {
  return fetch(`${API_BASE}/contas`).then(handleResponse);
}

export function getLancamentos() {
  return fetch(`${API_BASE}/lancamentos`).then(handleResponse);
}

export function criarLancamento(lancamento) {
  return fetch(`${API_BASE}/lancamentos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lancamento),
  }).then(handleResponse);
}

export function uploadLancamentos(arquivo) {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  return fetch(`${API_BASE}/lancamentos/upload`, {
    method: "POST",
    body: formData,
  }).then(handleResponse);
}

export function getBalancete() {
  return fetch(`${API_BASE}/relatorios/balancete`).then(handleResponse);
}

export function getBP() {
  return fetch(`${API_BASE}/relatorios/bp`).then(handleResponse);
}

export function getDRE() {
  return fetch(`${API_BASE}/relatorios/dre`).then(handleResponse);
}
```

- [ ] **Step 5: Create the placeholder pages**

`frontend/src/pages/Lancamentos.jsx`:

```jsx
export default function Lancamentos() {
  return <p>Em construção.</p>;
}
```

`frontend/src/pages/Balancete.jsx`:

```jsx
export default function Balancete() {
  return <p>Em construção.</p>;
}
```

`frontend/src/pages/BalancoPatrimonial.jsx`:

```jsx
export default function BalancoPatrimonial() {
  return <p>Em construção.</p>;
}
```

`frontend/src/pages/DRE.jsx`:

```jsx
export default function DRE() {
  return <p>Em construção.</p>;
}
```

- [ ] **Step 6: Create `frontend/src/App.jsx`**

```jsx
import { useState } from "react";
import Lancamentos from "./pages/Lancamentos";
import Balancete from "./pages/Balancete";
import BalancoPatrimonial from "./pages/BalancoPatrimonial";
import DRE from "./pages/DRE";

const ABAS = {
  lancamentos: { rotulo: "Lançamentos", componente: Lancamentos },
  balancete: { rotulo: "Balancete", componente: Balancete },
  bp: { rotulo: "Balanço Patrimonial", componente: BalancoPatrimonial },
  dre: { rotulo: "DRE", componente: DRE },
};

export default function App() {
  const [abaAtiva, setAbaAtiva] = useState("lancamentos");
  const Componente = ABAS[abaAtiva].componente;

  return (
    <div className="app">
      <nav className="tabs">
        {Object.entries(ABAS).map(([chave, { rotulo }]) => (
          <button
            key={chave}
            className={chave === abaAtiva ? "tab tab-ativa" : "tab"}
            onClick={() => setAbaAtiva(chave)}
          >
            {rotulo}
          </button>
        ))}
      </nav>
      <main>
        <Componente />
      </main>
    </div>
  );
}
```

- [ ] **Step 7: Create `frontend/src/index.css`**

```css
body {
  font-family: system-ui, sans-serif;
  margin: 0;
  background: #f5f5f5;
}

.tabs {
  display: flex;
  gap: 4px;
  background: #1f2937;
  padding: 8px;
}

.tab {
  background: transparent;
  color: white;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 4px;
}

.tab-ativa {
  background: #374151;
  font-weight: bold;
}

main {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

th, td {
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid #ddd;
}

.erro {
  color: #b91c1c;
}

.total-linha {
  font-weight: bold;
  border-top: 2px solid #333;
}
```

- [ ] **Step 8: Create `frontend/src/main.jsx`**

```jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 9: Install dependencies and build**

Run: `cd frontend && npm install && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 10: Manually verify in the browser**

Run: `npm run dev` (from `frontend/`), open `http://localhost:5173`. Confirm the four tabs render and clicking each one shows its "Em construção." placeholder. Leave the backend running (`uvicorn app.main:app --reload` from `backend/`) — this isn't required yet since the placeholders don't call the API, but will be from Task 9 onward.

- [ ] **Step 11: Commit**

```bash
git add frontend
git commit -m "feat: scaffold React frontend with tab navigation and API client"
```

---

## Task 9: Lançamentos page (form, CSV upload, table)

**Files:**
- Modify: `frontend/src/pages/Lancamentos.jsx` (replace placeholder with full implementation)

**Interfaces:**
- Consumes: `getContas`, `getLancamentos`, `criarLancamento`, `uploadLancamentos` (`frontend/src/api.js`, from Task 8)

- [ ] **Step 1: Replace `frontend/src/pages/Lancamentos.jsx`**

```jsx
import { useEffect, useState } from "react";
import { getContas, getLancamentos, criarLancamento, uploadLancamentos } from "../api";

const LANCAMENTO_VAZIO = {
  data: "",
  conta_debito: "",
  conta_credito: "",
  valor: "",
  historico: "",
};

export default function Lancamentos() {
  const [contas, setContas] = useState([]);
  const [lancamentos, setLancamentos] = useState([]);
  const [form, setForm] = useState(LANCAMENTO_VAZIO);
  const [erroForm, setErroForm] = useState(null);
  const [resultadoUpload, setResultadoUpload] = useState(null);

  async function carregarDados() {
    const [contasResp, lancamentosResp] = await Promise.all([getContas(), getLancamentos()]);
    setContas(contasResp);
    setLancamentos(lancamentosResp);
  }

  useEffect(() => {
    carregarDados();
  }, []);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErroForm(null);
    try {
      await criarLancamento({ ...form, valor: parseFloat(form.valor) });
      setForm(LANCAMENTO_VAZIO);
      await carregarDados();
    } catch (erro) {
      setErroForm(erro.message);
    }
  }

  async function aoSelecionarArquivo(evento) {
    const arquivo = evento.target.files[0];
    if (!arquivo) return;
    const resultado = await uploadLancamentos(arquivo);
    setResultadoUpload(resultado);
    await carregarDados();
    evento.target.value = "";
  }

  return (
    <section>
      <h2>Lançamentos</h2>

      <form onSubmit={aoSubmeter}>
        <label>
          Data
          <input
            type="date"
            value={form.data}
            onChange={(e) => setForm({ ...form, data: e.target.value })}
            required
          />
        </label>
        <label>
          Conta débito
          <select
            value={form.conta_debito}
            onChange={(e) => setForm({ ...form, conta_debito: e.target.value })}
            required
          >
            <option value="">Selecione</option>
            {contas.map((conta) => (
              <option key={conta.codigo} value={conta.codigo}>
                {conta.codigo} - {conta.nome}
              </option>
            ))}
          </select>
        </label>
        <label>
          Conta crédito
          <select
            value={form.conta_credito}
            onChange={(e) => setForm({ ...form, conta_credito: e.target.value })}
            required
          >
            <option value="">Selecione</option>
            {contas.map((conta) => (
              <option key={conta.codigo} value={conta.codigo}>
                {conta.codigo} - {conta.nome}
              </option>
            ))}
          </select>
        </label>
        <label>
          Valor
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={form.valor}
            onChange={(e) => setForm({ ...form, valor: e.target.value })}
            required
          />
        </label>
        <label>
          Histórico
          <input
            type="text"
            value={form.historico}
            onChange={(e) => setForm({ ...form, historico: e.target.value })}
          />
        </label>
        <button type="submit">Lançar</button>
      </form>
      {erroForm && <p className="erro">{erroForm}</p>}

      <h3>Importar CSV</h3>
      <p>Colunas esperadas: data, conta_debito, conta_credito, valor, historico</p>
      <input type="file" accept=".csv" onChange={aoSelecionarArquivo} />
      {resultadoUpload && (
        <div>
          <p>{resultadoUpload.inseridos} lançamento(s) inserido(s).</p>
          {resultadoUpload.erros.length > 0 && (
            <ul className="erro">
              {resultadoUpload.erros.map((erro) => (
                <li key={erro.linha}>
                  Linha {erro.linha}: {erro.motivo}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <h3>Lançamentos existentes</h3>
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Débito</th>
            <th>Crédito</th>
            <th>Valor</th>
            <th>Histórico</th>
          </tr>
        </thead>
        <tbody>
          {lancamentos.map((lancamento) => (
            <tr key={lancamento.id}>
              <td>{lancamento.data}</td>
              <td>{lancamento.conta_debito}</td>
              <td>{lancamento.conta_credito}</td>
              <td>{lancamento.valor.toFixed(2)}</td>
              <td>{lancamento.historico}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 3: Manually verify in the browser**

With the backend running (`uvicorn app.main:app --reload` from `backend/`) and `npm run dev` running from `frontend/`: open the Lançamentos tab, confirm the account dropdowns are populated from `/contas`, create one manual lançamento and confirm it appears in the table below, then upload a small CSV with one valid and one invalid row and confirm the error message shows the right line number and reason.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Lancamentos.jsx
git commit -m "feat: implement lancamentos page with manual entry and CSV upload"
```

---

## Task 10: Balancete page

**Files:**
- Modify: `frontend/src/pages/Balancete.jsx` (replace placeholder with full implementation)

**Interfaces:**
- Consumes: `getBalancete` (`frontend/src/api.js`, from Task 8)

- [ ] **Step 1: Replace `frontend/src/pages/Balancete.jsx`**

```jsx
import { useEffect, useState } from "react";
import { getBalancete } from "../api";

export default function Balancete() {
  const [linhas, setLinhas] = useState([]);

  useEffect(() => {
    getBalancete().then(setLinhas);
  }, []);

  return (
    <section>
      <h2>Balancete</h2>
      <table>
        <thead>
          <tr>
            <th>Conta</th>
            <th>Grupo</th>
            <th>Total débito</th>
            <th>Total crédito</th>
            <th>Saldo</th>
          </tr>
        </thead>
        <tbody>
          {linhas.map((linha) => (
            <tr key={linha.codigo}>
              <td>{linha.codigo} - {linha.nome}</td>
              <td>{linha.grupo}</td>
              <td>{linha.total_debito.toFixed(2)}</td>
              <td>{linha.total_credito.toFixed(2)}</td>
              <td>{linha.saldo.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 3: Manually verify in the browser**

Open the Balancete tab and confirm it lists all 20 accounts with the correct saldo for any lançamentos created in Task 9.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Balancete.jsx
git commit -m "feat: implement balancete page"
```

---

## Task 11: Balanço Patrimonial page

**Files:**
- Modify: `frontend/src/pages/BalancoPatrimonial.jsx` (replace placeholder with full implementation)

**Interfaces:**
- Consumes: `getBP` (`frontend/src/api.js`, from Task 8)

- [ ] **Step 1: Replace `frontend/src/pages/BalancoPatrimonial.jsx`**

```jsx
import { useEffect, useState } from "react";
import { getBP } from "../api";

function Coluna({ titulo, secoes, total }) {
  return (
    <div>
      <h3>{titulo}</h3>
      {secoes.map((secao) => (
        <div key={secao.grupo}>
          <h4>{secao.grupo}</h4>
          <table>
            <tbody>
              {secao.contas.map((conta) => (
                <tr key={conta.codigo}>
                  <td>{conta.nome}</td>
                  <td>{conta.saldo.toFixed(2)}</td>
                </tr>
              ))}
              <tr className="total-linha">
                <td>Subtotal</td>
                <td>{secao.subtotal.toFixed(2)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}
      <p className="total-linha">Total: {total.toFixed(2)}</p>
    </div>
  );
}

export default function BalancoPatrimonial() {
  const [bp, setBp] = useState(null);

  useEffect(() => {
    getBP().then(setBp);
  }, []);

  if (!bp) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Balanço Patrimonial</h2>
      {!bp.balanceado && (
        <p className="erro">
          Atenção: Ativo ({bp.total_ativo.toFixed(2)}) não bate com Passivo + PL ({bp.total_passivo_pl.toFixed(2)}).
        </p>
      )}
      <div style={{ display: "flex", gap: "32px" }}>
        <Coluna titulo="Ativo" secoes={bp.ativo} total={bp.total_ativo} />
        <Coluna titulo="Passivo + Patrimônio Líquido" secoes={bp.passivo_pl} total={bp.total_passivo_pl} />
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 3: Manually verify in the browser**

Open the Balanço Patrimonial tab and confirm Ativo and Passivo + PL are shown side by side, grouped correctly, and the two totals match (no warning message shown).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/BalancoPatrimonial.jsx
git commit -m "feat: implement balanco patrimonial page"
```

---

## Task 12: DRE page

**Files:**
- Modify: `frontend/src/pages/DRE.jsx` (replace placeholder with full implementation)

**Interfaces:**
- Consumes: `getDRE` (`frontend/src/api.js`, from Task 8)

- [ ] **Step 1: Replace `frontend/src/pages/DRE.jsx`**

```jsx
import { useEffect, useState } from "react";
import { getDRE } from "../api";

export default function DRE() {
  const [dre, setDre] = useState(null);

  useEffect(() => {
    getDRE().then(setDre);
  }, []);

  if (!dre) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Demonstração de Resultado do Exercício</h2>

      <h3>Receitas</h3>
      <table>
        <tbody>
          {dre.receitas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td>{conta.valor.toFixed(2)}</td>
            </tr>
          ))}
          <tr className="total-linha">
            <td>Total de receitas</td>
            <td>{dre.total_receitas.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      <h3>Despesas</h3>
      <table>
        <tbody>
          {dre.despesas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td>{conta.valor.toFixed(2)}</td>
            </tr>
          ))}
          <tr className="total-linha">
            <td>Total de despesas</td>
            <td>{dre.total_despesas.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      <p className="total-linha">
        Resultado do período: {dre.resultado_periodo.toFixed(2)}
        {dre.resultado_periodo >= 0 ? " (lucro)" : " (prejuízo)"}
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 3: Manually verify in the browser**

Open the DRE tab and confirm receitas/despesas are listed with correct totals and the resultado do período matches `total_receitas - total_despesas`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DRE.jsx
git commit -m "feat: implement DRE page"
```

---

## Task 13: README and end-to-end manual QA

**Files:**
- Create: `README.md`

**Interfaces:**
- None (documentation + manual verification only).

- [ ] **Step 1: Create `README.md`**

```markdown
# Contabilidade Web

Aplicação de portfólio que replica o ciclo contábil básico (lançamento →
balancete → Balanço Patrimonial e DRE) com FastAPI + pandas no backend
e React no frontend.

## Rodando o backend

    cd backend
    python -m venv .venv
    .venv/Scripts/activate   # Windows; no POSIX: source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

A API sobe em http://localhost:8000. Os testes: `pytest -v`.

## Rodando o frontend

    cd frontend
    npm install
    npm run dev

O app sobe em http://localhost:5173.

## Checklist de verificação manual (end-to-end)

- [ ] Backend e frontend rodando simultaneamente
- [ ] Aba Lançamentos: dropdowns de conta populados
- [ ] Criar um lançamento manual (ex: débito Caixa, crédito Capital
      Social) e ver aparecer na tabela
- [ ] Upload de CSV com uma linha válida e uma com conta inexistente:
      confirmar que a válida entrou e o erro aponta a linha certa
- [ ] Aba Balancete: saldo da conta lançada bate com o valor informado
- [ ] Aba Balanço Patrimonial: Ativo fecha com Passivo + PL (sem aviso
      de desbalanceamento)
- [ ] Aba DRE: lançar uma receita e uma despesa, conferir que o
      resultado do período é receita - despesa
```

- [ ] **Step 2: Run the full backend test suite one more time**

Run: `cd backend && pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Walk through the manual QA checklist in the README**

Follow every item in the checklist above with both servers running; fix anything that doesn't match before considering the project done.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add README with run instructions and manual QA checklist"
```
