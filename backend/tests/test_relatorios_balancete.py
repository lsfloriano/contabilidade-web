from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import calcular_balancete, montar_balancete


def test_calcular_balancete_soma_debitos_e_creditos(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 10), conta_debito="1.1.04", conta_credito="1.1.01", valor=Decimal("300.00"), historico="Compra de estoque à vista"),
    ])
    db_session.commit()

    balancete = calcular_balancete(db_session)

    caixa = next(c for c in balancete if c["codigo"] == "1.1.01")
    assert caixa["total_debito"] == 1000.00
    assert caixa["total_credito"] == 300.00
    assert caixa["saldo"] == 700.00  # devedora: debito - credito

    capital = next(c for c in balancete if c["codigo"] == "2.3.01")
    assert capital["saldo"] == 1000.00  # credora: credito - debito

    estoques = next(c for c in balancete if c["codigo"] == "1.1.04")
    assert estoques["saldo"] == 300.00


def test_calcular_balancete_sem_lancamentos_retorna_zerado(db_session):
    balancete = calcular_balancete(db_session)
    assert len(balancete) == 20
    assert all(c["saldo"] == 0.0 for c in balancete)


def test_montar_balancete_totais_fecham_por_partida_dobrada(db_session):
    # Cada lançamento credita uma conta e debita outra pelo mesmo valor, então
    # Σdébitos == Σcréditos por construção — é o que o balancete existe para
    # provar. Três lançamentos com valores distintos, nenhum repetindo par de
    # contas, para não mascarar um bug de agrupamento errado.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00")),
        Lancamento(data=date(2026, 1, 10), conta_debito="1.1.04", conta_credito="1.1.01", valor=Decimal("300.00")),
        Lancamento(data=date(2026, 1, 15), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("50.00")),
    ])
    db_session.commit()

    balancete = montar_balancete(db_session)

    assert balancete["total_debito"] == 1350.00
    assert balancete["total_credito"] == 1350.00
    assert len(balancete["linhas"]) == 20


def test_montar_balancete_sem_lancamentos_totais_zerados(db_session):
    balancete = montar_balancete(db_session)
    assert balancete["total_debito"] == 0.0
    assert balancete["total_credito"] == 0.0


def test_calcular_balancete_filtra_por_intervalo(db_session):
    # Três lançamentos idênticos exceto pela data: um antes do início, um
    # dentro, um depois do fim. Só o do meio pode contar.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00")),
        Lancamento(data=date(2026, 2, 15), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("200.00")),
        Lancamento(data=date(2026, 3, 1), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("40.00")),
    ])
    db_session.commit()

    balancete = calcular_balancete(
        db_session, data_inicio=date(2026, 2, 1), data_fim=date(2026, 2, 28)
    )

    caixa = next(c for c in balancete if c["codigo"] == "1.1.01")
    assert caixa["total_debito"] == 200.00
    assert caixa["total_credito"] == 0.00
    assert caixa["saldo"] == 200.00

    capital = next(c for c in balancete if c["codigo"] == "2.3.01")
    assert capital["saldo"] == 200.00

    # O plano de contas inteiro continua na lista; conta sem lançamento no
    # recorte aparece zerada, não some. É essa propriedade que garante que os
    # dois períodos de uma comparação tenham sempre as mesmas linhas.
    assert len(balancete) == 20
    estoques = next(c for c in balancete if c["codigo"] == "1.1.04")
    assert estoques["saldo"] == 0.0


def test_calcular_balancete_intervalo_inclui_as_datas_de_borda(db_session):
    # As duas pontas são inclusivas: data >= inicio E data <= fim.
    db_session.add_all([
        Lancamento(data=date(2026, 2, 1), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("100.00")),
        Lancamento(data=date(2026, 2, 28), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("25.00")),
    ])
    db_session.commit()

    balancete = calcular_balancete(
        db_session, data_inicio=date(2026, 2, 1), data_fim=date(2026, 2, 28)
    )

    caixa = next(c for c in balancete if c["codigo"] == "1.1.01")
    assert caixa["saldo"] == 125.00


def test_calcular_balancete_sem_parametros_soma_todos_os_periodos(db_session):
    # Regressão: os parâmetros novos são opcionais e o padrão é não filtrar
    # nada — nem por data futura. É o que mantém Balancete, BP, DRE e Análise
    # com o comportamento de hoje.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00")),
        Lancamento(data=date(2026, 2, 15), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("200.00")),
        Lancamento(data=date(2099, 12, 31), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("40.00")),
    ])
    db_session.commit()

    balancete = calcular_balancete(db_session)

    caixa = next(c for c in balancete if c["codigo"] == "1.1.01")
    assert caixa["total_debito"] == 1240.00
    assert caixa["saldo"] == 1240.00

    capital = next(c for c in balancete if c["codigo"] == "2.3.01")
    assert capital["saldo"] == 1240.00


def test_endpoint_balancete(client, db_session):
    db_session.add(Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00")))
    db_session.commit()

    resposta = client.get("/relatorios/balancete")
    assert resposta.status_code == 200
    corpo = resposta.json()
    caixa = next(l for l in corpo["linhas"] if l["codigo"] == "1.1.01")
    assert caixa["saldo"] == 1000.00
    assert corpo["total_debito"] == 1000.00
    assert corpo["total_credito"] == 1000.00
