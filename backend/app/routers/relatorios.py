from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.relatorios import montar_balancete, montar_bp, montar_dre, montar_analise
from app.schemas import BalanceteReport, BPReport, DREReport, AnaliseReport

router = APIRouter(prefix="/relatorios")


@router.get("/balancete", response_model=BalanceteReport)
def obter_balancete(db: Session = Depends(get_db)):
    return montar_balancete(db)


# BP é foto: uma data de corte só, sem início — o saldo acumula desde o
# primeiro lançamento. Sem o parâmetro, soma a base inteira, como antes.
@router.get("/bp", response_model=BPReport)
def obter_bp(data_corte: date | None = None, db: Session = Depends(get_db)):
    return montar_bp(db, data_corte=data_corte)


# DRE é fluxo: um intervalo. Os dois parâmetros são independentes e opcionais;
# sem nenhum deles, o comportamento é o de hoje.
@router.get("/dre", response_model=DREReport)
def obter_dre(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
):
    return montar_dre(db, data_inicio=data_inicio, data_fim=data_fim)


@router.get("/analise", response_model=AnaliseReport)
def obter_analise(db: Session = Depends(get_db)):
    return montar_analise(db)
