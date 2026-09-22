from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import exigir_admin, hash_senha
from app.db import get_db
from app.models import Papel, Usuario
from app.schemas import UsuarioCreate, UsuarioOut

router = APIRouter()


@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_admin),
):
    return db.query(Usuario).order_by(Usuario.email).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=201)
def criar_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_admin),
):
    # E-mail normalizado para minúsculas antes de checar duplicata e de
    # gravar: sem isto, "Novo@..." e "novo@..." viram duas contas diferentes,
    # e a checagem de duplicata abaixo não pegaria a diferença de caixa.
    email_normalizado = payload.email.strip().lower()

    # A coluna já é unique; a checagem aqui é o que transforma o IntegrityError
    # (que viraria 500) numa recusa explicada, no mesmo 422 que o resto do app
    # usa para entrada inválida.
    if db.query(Usuario).filter_by(email=email_normalizado).first() is not None:
        raise HTTPException(status_code=422, detail=f"e-mail {email_normalizado} já cadastrado")

    usuario = Usuario(
        email=email_normalizado,
        nome=payload.nome,
        senha_hash=hash_senha(payload.senha),
        papel=Papel(payload.papel),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
