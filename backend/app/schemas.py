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


class BalanceteRow(BaseModel):
    codigo: str
    nome: str
    grupo: str
    tipo: str
    total_debito: float
    total_credito: float
    saldo: float


class BPConta(BaseModel):
    codigo: str
    nome: str
    saldo: float


class BPSecao(BaseModel):
    grupo: str
    contas: list[BPConta]
    subtotal: float


class BPReport(BaseModel):
    ativo: list[BPSecao]
    passivo_pl: list[BPSecao]
    total_ativo: float
    total_passivo_pl: float
    balanceado: bool
