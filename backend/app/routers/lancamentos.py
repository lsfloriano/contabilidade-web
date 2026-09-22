import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.auth import usuario_atual
from app.db import get_db
from app.models import Lancamento, Usuario
from app.schemas import (
    LancamentoCreate,
    LancamentoEstornoCreate,
    LancamentoOut,
    UploadErro,
    UploadResultado,
)
from app.validacao import validar_lancamento, LancamentoInvalido

router = APIRouter()


@router.post("/lancamentos", response_model=LancamentoOut, status_code=201)
def criar_lancamento(
    payload: LancamentoCreate,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    try:
        validar_lancamento(db, payload.conta_debito, payload.conta_credito, payload.valor)
    except LancamentoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    lancamento = Lancamento(**payload.model_dump())
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


def _historico_padrao_estorno(lancamento_id: int, historico_original: str | None) -> str:
    if historico_original:
        return f"Estorno do lançamento #{lancamento_id}: {historico_original}"
    return f"Estorno do lançamento #{lancamento_id}"


@router.post("/lancamentos/{lancamento_id}/estorno", response_model=LancamentoOut, status_code=201)
def estornar_lancamento(
    lancamento_id: int,
    payload: LancamentoEstornoCreate,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    original = db.query(Lancamento).filter_by(id=lancamento_id).first()
    if original is None:
        raise HTTPException(status_code=404, detail=f"lançamento #{lancamento_id} não existe")

    # O estorno é o reverso exato: os dois lados trocam, o valor é o mesmo.
    conta_debito = original.conta_credito
    conta_credito = original.conta_debito
    valor = float(original.valor)

    # A mesma validação de POST /lancamentos. Redundante na prática (o reverso
    # de um lançamento válido é sempre válido), mas sem custo e consistente.
    try:
        validar_lancamento(db, conta_debito, conta_credito, valor)
    except LancamentoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    lancamento = Lancamento(
        data=payload.data,
        conta_debito=conta_debito,
        conta_credito=conta_credito,
        valor=valor,
        historico=payload.historico or _historico_padrao_estorno(lancamento_id, original.historico),
        estorno_de=lancamento_id,
    )
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.get("/lancamentos", response_model=list[LancamentoOut])
def listar_lancamentos(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return db.query(Lancamento).order_by(Lancamento.data).all()


@router.post("/lancamentos/upload", response_model=UploadResultado)
async def upload_lancamentos(
    db: Session = Depends(get_db),
    arquivo: UploadFile = File(...),
    _usuario: Usuario = Depends(usuario_atual),
):
    conteudo = await arquivo.read()

    try:
        df = pd.read_csv(io.BytesIO(conteudo))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Arquivo CSV inválido: {exc}")

    inseridos = 0
    erros: list[UploadErro] = []

    for indice, linha in df.iterrows():
        numero_linha = indice + 2  # +1 for header row, +1 to make it 1-indexed

        try:
            conta_debito = str(linha["conta_debito"]).strip()
            conta_credito = str(linha["conta_credito"]).strip()
            valor = float(linha["valor"])
            data_lancamento = pd.to_datetime(linha["data"]).date()
            validar_lancamento(db, conta_debito, conta_credito, valor)
        except (LancamentoInvalido, KeyError, ValueError, TypeError) as exc:
            erros.append(UploadErro(linha=numero_linha, motivo=str(exc)))
            continue

        historico = linha.get("historico")
        db.add(Lancamento(
            data=data_lancamento,
            conta_debito=conta_debito,
            conta_credito=conta_credito,
            valor=valor,
            historico=None if pd.isna(historico) else historico,
        ))
        inseridos += 1

    db.commit()
    return UploadResultado(inseridos=inseridos, erros=erros)
