from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import criar_token, usuario_atual, verificar_senha
from app.db import get_db
from app.models import Usuario
from app.schemas import LoginRequest, LoginResponse, MeOut

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # E-mail é normalizado para minúsculas na comparação: o login não pode
    # depender de quem digitou "Admin@..." ou "admin@..." bater exatamente
    # com o que foi semeado/cadastrado.
    email_normalizado = payload.email.strip().lower()
    usuario = db.query(Usuario).filter_by(email=email_normalizado).first()
    # Mesma mensagem para e-mail inexistente e senha errada: não interessa
    # contar a quem tenta adivinhar qual dos dois ele acertou.
    if usuario is None or not verificar_senha(payload.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    return LoginResponse(
        token=criar_token(usuario.email),
        nome=usuario.nome,
        papel=usuario.papel.value,
    )


# A rota que o frontend chama ao abrir a página com um token guardado, para
# saber se ele ainda vale sem obrigar login de novo.
@router.get("/me", response_model=MeOut)
def me(usuario: Usuario = Depends(usuario_atual)):
    return usuario
