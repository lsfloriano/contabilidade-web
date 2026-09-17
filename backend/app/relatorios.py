import pandas as pd
from sqlalchemy.orm import Session

from app.models import Lancamento, ContaContabil, Natureza, Grupo, TipoConta


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


GRUPOS_ATIVO = [Grupo.ativo_circulante.value, Grupo.ativo_nao_circulante.value]
GRUPOS_PASSIVO_PL = [Grupo.passivo_circulante.value, Grupo.passivo_nao_circulante.value, Grupo.patrimonio_liquido.value]


def _agrupar_secoes(contas: list[dict], grupos: list[str]) -> tuple[list[dict], float]:
    secoes = []
    total = 0.0
    for grupo in grupos:
        contas_grupo = [c for c in contas if c["grupo"] == grupo]
        subtotal = sum(c["saldo"] for c in contas_grupo)
        total += subtotal
        secoes.append({
            "grupo": grupo,
            "contas": [{"codigo": c["codigo"], "nome": c["nome"], "saldo": c["saldo"]} for c in contas_grupo],
            "subtotal": subtotal,
        })
    return secoes, total


def montar_bp(db: Session) -> dict:
    balancete = calcular_balancete(db)
    patrimoniais = [c for c in balancete if c["tipo"] == TipoConta.patrimonial.value]
    resultado = [c for c in balancete if c["tipo"] == TipoConta.resultado.value]

    ativo_secoes, total_ativo = _agrupar_secoes(patrimoniais, GRUPOS_ATIVO)
    passivo_pl_secoes, total_passivo_pl = _agrupar_secoes(patrimoniais, GRUPOS_PASSIVO_PL)

    total_receitas = sum(c["saldo"] for c in resultado if c["grupo"] == Grupo.receita.value)
    total_despesas = sum(c["saldo"] for c in resultado if c["grupo"] == Grupo.despesa.value)
    resultado_periodo = total_receitas - total_despesas

    patrimonio_liquido = next(s for s in passivo_pl_secoes if s["grupo"] == Grupo.patrimonio_liquido.value)
    patrimonio_liquido["contas"].append({
        "codigo": "RESULTADO",
        "nome": "Resultado do Exercício (não realizado)",
        "saldo": resultado_periodo,
    })
    patrimonio_liquido["subtotal"] += resultado_periodo
    total_passivo_pl += resultado_periodo

    return {
        "ativo": ativo_secoes,
        "passivo_pl": passivo_pl_secoes,
        "total_ativo": total_ativo,
        "total_passivo_pl": total_passivo_pl,
        "balanceado": abs(total_ativo - total_passivo_pl) < 0.01,
    }


def montar_dre(db: Session) -> dict:
    balancete = calcular_balancete(db)
    resultado_contas = [c for c in balancete if c["tipo"] == TipoConta.resultado.value]

    receitas = [c for c in resultado_contas if c["grupo"] == Grupo.receita.value]
    despesas = [c for c in resultado_contas if c["grupo"] == Grupo.despesa.value]

    total_receitas = sum(c["saldo"] for c in receitas)
    total_despesas = sum(c["saldo"] for c in despesas)

    return {
        "receitas": [{"codigo": c["codigo"], "nome": c["nome"], "valor": c["saldo"]} for c in receitas],
        "despesas": [{"codigo": c["codigo"], "nome": c["nome"], "valor": c["saldo"]} for c in despesas],
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_periodo": total_receitas - total_despesas,
    }
