from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str
    natureza: str
    grupo: str
    tipo: str


class LancamentoCreate(BaseModel):
    data: date
    conta_debito: str
    conta_credito: str
    valor: float
    historico: Optional[str] = None


class LancamentoOut(LancamentoCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
