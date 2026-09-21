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


def test_montar_dre_filtra_por_intervalo(db_session):
    db_session.add_all([
        # Receita antes do início: fora.
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("1000.00"), historico="Venda de janeiro"),
        # Dentro do intervalo.
        Lancamento(data=date(2026, 2, 10), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00"), historico="Venda de fevereiro"),
        Lancamento(data=date(2026, 2, 20), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00"), historico="Baixa de CMV"),
        # Despesa depois do fim: fora.
        Lancamento(data=date(2026, 3, 1), conta_debito="4.1.02", conta_credito="1.1.01", valor=Decimal("500.00"), historico="Aluguel de março"),
    ])
    db_session.commit()

    dre = montar_dre(db_session, data_inicio=date(2026, 2, 1), data_fim=date(2026, 2, 28))

    assert dre["total_receitas"] == 3000.00
    assert dre["total_despesas"] == 1200.00
    assert dre["resultado_periodo"] == 1800.00

    # As linhas não somem no recorte: a conta fora do intervalo aparece zerada.
    # É o que garante que os dois períodos da comparação casem linha a linha.
    assert len(dre["receitas"]) == 2
    assert len(dre["despesas"]) == 5
    administrativas = next(c for c in dre["despesas"] if c["codigo"] == "4.1.02")
    assert administrativas["valor"] == 0.0


def test_montar_dre_sem_parametros_soma_todos_os_periodos(db_session):
    # Regressão: sem intervalo, a DRE continua sendo o período contínuo único
    # de hoje — acumula tudo desde o primeiro lançamento.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("1000.00")),
        Lancamento(data=date(2026, 2, 10), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00")),
        Lancamento(data=date(2026, 2, 20), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00")),
        Lancamento(data=date(2026, 3, 1), conta_debito="4.1.02", conta_credito="1.1.01", valor=Decimal("500.00")),
    ])
    db_session.commit()

    dre = montar_dre(db_session)

    assert dre["total_receitas"] == 4000.00
    assert dre["total_despesas"] == 1700.00
    assert dre["resultado_periodo"] == 2300.00


def test_endpoint_dre(client):
    client.post("/lancamentos", json={"data": "2026-01-03", "conta_debito": "1.1.03", "conta_credito": "3.1.01", "valor": 500.0})

    resposta = client.get("/relatorios/dre")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resultado_periodo"] == 500.0
