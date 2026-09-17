from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import calcular_balancete


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


def test_endpoint_balancete(client, db_session):
    db_session.add(Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("1000.00")))
    db_session.commit()

    resposta = client.get("/relatorios/balancete")
    assert resposta.status_code == 200
    linhas = resposta.json()
    caixa = next(l for l in linhas if l["codigo"] == "1.1.01")
    assert caixa["saldo"] == 1000.00
