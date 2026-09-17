import pandas as pd
from sqlalchemy.orm import Session

from app.models import Lancamento, ContaContabil, Natureza


def _lancamentos_dataframe(db: Session) -> pd.DataFrame:
    lancamentos = db.query(Lancamento).all()
    rows = [
        {"conta_debito": l.conta_debito, "conta_credito": l.conta_credito, "valor": float(l.valor)}
        for l in lancamentos
    ]
    return pd.DataFrame(rows, columns=["conta_debito", "conta_credito", "valor"])


def _contas_dataframe(db: Session) -> pd.DataFrame:
    contas = db.query(ContaContabil).all()
    return pd.DataFrame([
        {
            "codigo": c.codigo,
            "nome": c.nome,
            "natureza": c.natureza.value,
            "grupo": c.grupo.value,
            "tipo": c.tipo.value,
        }
        for c in contas
    ])


def calcular_balancete(db: Session) -> list[dict]:
    lanc_df = _lancamentos_dataframe(db)
    contas_df = _contas_dataframe(db)

    if lanc_df.empty:
        debitos = pd.Series(dtype=float)
        creditos = pd.Series(dtype=float)
    else:
        debitos = lanc_df.groupby("conta_debito")["valor"].sum()
        creditos = lanc_df.groupby("conta_credito")["valor"].sum()

    resultado = []
    for _, conta in contas_df.iterrows():
        total_debito = float(debitos.get(conta["codigo"], 0.0))
        total_credito = float(creditos.get(conta["codigo"], 0.0))

        if conta["natureza"] == Natureza.devedora.value:
            saldo = total_debito - total_credito
        else:
            saldo = total_credito - total_debito

        resultado.append({
            "codigo": conta["codigo"],
            "nome": conta["nome"],
            "grupo": conta["grupo"],
            "tipo": conta["tipo"],
            "total_debito": total_debito,
            "total_credito": total_credito,
            "saldo": saldo,
        })
    return resultado
