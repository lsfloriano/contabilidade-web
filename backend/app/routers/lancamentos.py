import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Lancamento
from app.schemas import LancamentoCreate, LancamentoOut, UploadErro, UploadResultado
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
