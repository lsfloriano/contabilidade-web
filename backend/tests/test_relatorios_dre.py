from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import montar_dre


def test_montar_dre_calcula_resultado(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 3), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00"), historico="Venda a prazo"),
        Lancamento(data=date(2026, 1, 3), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00"), historico="Baixa de CMV"),
    ])
    db_session.commit()

    dre = montar_dre(db_session)

    assert dre["total_receitas"] == 3000.00
    assert dre["total_despesas"] == 1200.00
    assert dre["resultado_periodo"] == 1800.00

    receita_vendas = next(c for c in dre["receitas"] if c["codigo"] == "3.1.01")
    assert receita_vendas["valor"] == 3000.00


def test_endpoint_dre(client):
    client.post("/lancamentos", json={"data": "2026-01-03", "conta_debito": "1.1.03", "conta_credito": "3.1.01", "valor": 500.0})

    resposta = client.get("/relatorios/dre")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resultado_periodo"] == 500.0
