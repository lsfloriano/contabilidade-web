from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import usuario_atual
from app.db import get_db
from app.models import Usuario
from app.relatorios import (
    montar_balancete,
    montar_balancete_planilha,
    montar_bp,
    montar_bp_planilha,
    montar_dre,
    montar_dre_planilha,
    montar_dfc,
    montar_analise,
)
from app.schemas import BalanceteReport, BPReport, DREReport, DFCReport, AnaliseReport

router = APIRouter(prefix="/relatorios")


def _xlsx_resposta(df, nome_aba: str, nome_arquivo: str) -> StreamingResponse:
    buffer = BytesIO()
    df.to_excel(buffer, sheet_name=nome_aba, index=False, engine="openpyxl")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=" + nome_arquivo},
    )


@router.get("/balancete/exportar")
def exportar_balancete(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return _xlsx_resposta(montar_balancete_planilha(db), "Balancete", "balancete.xlsx")


@router.get("/bp/exportar")
def exportar_bp(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return _xlsx_resposta(montar_bp_planilha(db), "Balanço Patrimonial", "balanco_patrimonial.xlsx")


@router.get("/dre/exportar")
def exportar_dre(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return _xlsx_resposta(montar_dre_planilha(db), "DRE", "dre.xlsx")


@router.get("/balancete", response_model=BalanceteReport)
def obter_balancete(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return montar_balancete(db)


# BP é foto: uma data de corte só, sem início — o saldo acumula desde o
# primeiro lançamento. Sem o parâmetro, soma a base inteira, como antes.
@router.get("/bp", response_model=BPReport)
def obter_bp(
    data_corte: date | None = None,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return montar_bp(db, data_corte=data_corte)


# DRE é fluxo: um intervalo. Os dois parâmetros são independentes e opcionais;
# sem nenhum deles, o comportamento é o de hoje.
@router.get("/dre", response_model=DREReport)
def obter_dre(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return montar_dre(db, data_inicio=data_inicio, data_fim=data_fim)


# DFC não tem filtro de data: segue a convenção de Balancete/BP/DRE antes da
# Comparação existir — acumula desde o primeiro lançamento.
@router.get("/dfc", response_model=DFCReport)
def obter_dfc(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return montar_dfc(db)


@router.get("/analise", response_model=AnaliseReport)
def obter_analise(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return montar_analise(db)
