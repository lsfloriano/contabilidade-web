import enum

from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Natureza(str, enum.Enum):
    devedora = "devedora"
    credora = "credora"


class Grupo(str, enum.Enum):
    ativo_circulante = "Ativo Circulante"
    ativo_nao_circulante = "Ativo Não Circulante"
    passivo_circulante = "Passivo Circulante"
    passivo_nao_circulante = "Passivo Não Circulante"
    patrimonio_liquido = "Patrimônio Líquido"
    receita = "Receita"
    despesa = "Despesa"


class TipoConta(str, enum.Enum):
    patrimonial = "patrimonial"
    resultado = "resultado"


class ContaContabil(Base):
    __tablename__ = "plano_de_contas"

    codigo = Column(String, primary_key=True)
    nome = Column(String, nullable=False)
    natureza = Column(Enum(Natureza), nullable=False)
    grupo = Column(Enum(Grupo), nullable=False)
    tipo = Column(Enum(TipoConta), nullable=False)


class Lancamento(Base):
    __tablename__ = "lancamentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
    conta_debito = Column(String, ForeignKey("plano_de_contas.codigo"), nullable=False)
    conta_credito = Column(String, ForeignKey("plano_de_contas.codigo"), nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    historico = Column(String, nullable=True)

    # Só o estorno tem este campo preenchido, apontando para o lançamento que
    # ele reverte. O original não ganha flag nenhuma: "foi estornado?" se
    # deriva de existir outro lançamento com estorno_de == id dele.
    estorno_de = Column(Integer, ForeignKey("lancamentos.id"), nullable=True)

    debito = relationship("ContaContabil", foreign_keys=[conta_debito])
    credito = relationship("ContaContabil", foreign_keys=[conta_credito])
