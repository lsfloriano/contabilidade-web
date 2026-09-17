from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.relatorios import calcular_balancete
from app.schemas import BalanceteRow

router = APIRouter(prefix="/relatorios")


@router.get("/balancete", response_model=list[BalanceteRow])
def obter_balancete(db: Session = Depends(get_db)):
    return calcular_balancete(db)
