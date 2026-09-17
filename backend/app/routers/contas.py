from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ContaContabil
from app.schemas import ContaOut

router = APIRouter()


@router.get("/contas", response_model=list[ContaOut])
def listar_contas(db: Session = Depends(get_db)):
    return db.query(ContaContabil).order_by(ContaContabil.codigo).all()
