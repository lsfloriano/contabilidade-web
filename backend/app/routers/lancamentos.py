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
