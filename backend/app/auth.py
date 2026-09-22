import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Papel, Usuario

# Mesmo padrão de DATABASE_URL em db.py: variável de ambiente com um padrão
# de demonstração embutido, para o app subir sem configuração nenhuma.
SEGREDO_JWT = os.environ.get("JWT_SECRET", "contabilidade-web-segredo-de-demonstracao")
ALGORITMO_JWT = "HS256"
HORAS_DE_VALIDADE = 24


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


# `horas` é parâmetro (e não constante fechada) para o teste conseguir montar
# um token já vencido — horas=-1 — sem esperar 24h de verdade.
def criar_token(email: str, horas: int = HORAS_DE_VALIDADE) -> str:
    expiracao = datetime.now(timezone.utc) + timedelta(hours=horas)
    return jwt.encode(
        {"sub": email, "exp": expiracao},
        SEGREDO_JWT,
        algorithm=ALGORITMO_JWT,
    )


# Devolve o e-mail gravado em `sub`, ou None se o token for malformado,
# assinado com outro segredo ou expirado. Um retorno só para os três casos:
# do ponto de vista de quem chama, todos viram o mesmo 401.
def decodificar_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SEGREDO_JWT, algorithms=[ALGORITMO_JWT])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")


# O token carrega só o e-mail: o papel vem do banco, agora, não de uma cópia
# gravada no login. Se o papel de alguém mudar, a mudança vale na requisição
# seguinte em vez de esperar o token velho expirar.
def usuario_atual(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    email = decodificar_token(authorization[len("Bearer "):])
    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    usuario = db.query(Usuario).filter_by(email=email).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    return usuario


def exigir_admin(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if usuario.papel != Papel.admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return usuario
