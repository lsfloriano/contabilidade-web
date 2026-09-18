from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.relatorios import calcular_balancete, montar_bp, montar_dre, montar_analise
from app.schemas import BalanceteRow, BPReport, DREReport, AnaliseReport

router = APIRouter(prefix="/relatorios")


@router.get("/balancete", response_model=list[BalanceteRow])
def obter_balancete(db: Session = Depends(get_db)):
    return calcular_balancete(db)


@router.get("/bp", response_model=BPReport)
def obter_bp(db: Session = Depends(get_db)):
    return montar_bp(db)


@router.get("/dre", response_model=DREReport)
def obter_dre(db: Session = Depends(get_db)):
    return montar_dre(db)


@router.get("/analise", response_model=AnaliseReport)
def obter_analise(db: Session = Depends(get_db)):
    return montar_analise(db)
