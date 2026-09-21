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
    estorno_de: Optional[int] = None


class LancamentoEstornoCreate(BaseModel):
    # O estorno não escolhe contas nem valor: os três saem invertidos/iguais
    # do lançamento original. Só data e histórico são do usuário.
    data: date
    historico: Optional[str] = None


class BalanceteRow(BaseModel):
    codigo: str
    nome: str
    grupo: str
    tipo: str
    total_debito: float
    total_credito: float
    saldo: float


class BalanceteReport(BaseModel):
    linhas: list[BalanceteRow]
    total_debito: float
    total_credito: float


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


class DREConta(BaseModel):
    codigo: str
    nome: str
    valor: float


class DREReport(BaseModel):
    receitas: list[DREConta]
    despesas: list[DREConta]
    total_receitas: float
    total_despesas: float
    resultado_periodo: float


class DFCConta(BaseModel):
    codigo: str
    nome: str
    valor: float


class DFCReport(BaseModel):
    operacionais: list[DFCConta]
    subtotal_operacionais: float
    investimentos: list[DFCConta]
    subtotal_investimentos: float
    financiamentos: list[DFCConta]
    subtotal_financiamentos: float
    variacao_liquida: float
    saldo_inicial: float
    saldo_final: float
    confere: bool


class UploadErro(BaseModel):
    linha: int
    motivo: str


class UploadResultado(BaseModel):
    inseridos: int
    erros: list[UploadErro]


class IndicadorOut(BaseModel):
    chave: str
    nome: str
    valor: Optional[float]
    formula: str
    numerador_nome: str
    numerador_valor: float
    denominador_nome: str
    denominador_valor: float
    direcao: str
    formato: str
    motivo: Optional[str] = None
    nao_significativo: bool = False
    observacao: Optional[str] = None


class FamiliaIndicadores(BaseModel):
    nome: str
    indicadores: list[IndicadorOut]


class AnaliseReport(BaseModel):
    familias: list[FamiliaIndicadores]
