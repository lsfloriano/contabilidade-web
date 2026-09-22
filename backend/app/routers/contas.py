from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import usuario_atual
from app.db import get_db
from app.models import ContaContabil, Usuario
from app.schemas import ContaOut

router = APIRouter()


@router.get("/contas", response_model=list[ContaOut])
def listar_contas(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(usuario_atual),
):
    return db.query(ContaContabil).order_by(ContaContabil.codigo).all()
