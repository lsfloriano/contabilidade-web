from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, init_db, SessionLocal
from app.seed import seed_plano_de_contas
from app.routers import contas, lancamentos


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(engine)
    db = SessionLocal()
    try:
        seed_plano_de_contas(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Contabilidade Web", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok"}


app.include_router(contas.router)
app.include_router(lancamentos.router)
