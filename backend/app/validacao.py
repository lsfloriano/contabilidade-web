from sqlalchemy.orm import Session

from app.models import ContaContabil


class LancamentoInvalido(ValueError):
    pass


def validar_lancamento(db: Session, conta_debito: str, conta_credito: str, valor: float) -> None:
    if valor is None or valor <= 0:
        raise LancamentoInvalido("valor deve ser maior que zero")

    if conta_debito == conta_credito:
        raise LancamentoInvalido("conta_debito e conta_credito devem ser diferentes")

    if db.query(ContaContabil).filter_by(codigo=conta_debito).first() is None:
        raise LancamentoInvalido(f"conta_debito '{conta_debito}' não existe no plano de contas")

    if db.query(ContaContabil).filter_by(codigo=conta_credito).first() is None:
        raise LancamentoInvalido(f"conta_credito '{conta_credito}' não existe no plano de contas")
