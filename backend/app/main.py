import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, init_db, SessionLocal
from app.seed import seed_plano_de_contas, seed_usuarios
from app.routers import auth, contas, lancamentos, relatorios, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(engine)
    db = SessionLocal()
    try:
        seed_plano_de_contas(db)
        seed_usuarios(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Contabilidade Web", lifespan=lifespan)

# FRONTEND_ORIGINS: lista separada por vírgula (ex: deploy no Vercel).
# Sem a variável, mantém só o dev local.
_origens_extras = [
    origem.strip()
    for origem in os.environ.get("FRONTEND_ORIGINS", "").split(",")
    if origem.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", *_origens_extras],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(contas.router)
app.include_router(lancamentos.router)
app.include_router(relatorios.router)
app.include_router(usuarios.router)
