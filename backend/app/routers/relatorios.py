from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.relatorios import calcular_balancete, montar_bp
from app.schemas import BalanceteRow, BPReport

router = APIRouter(prefix="/relatorios")


@router.get("/balancete", response_model=list[BalanceteRow])
def obter_balancete(db: Session = Depends(get_db)):
    return calcular_balancete(db)


@router.get("/bp", response_model=BPReport)
def obter_bp(db: Session = Depends(get_db)):
    return montar_bp(db)
