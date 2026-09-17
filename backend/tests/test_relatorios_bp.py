from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import montar_bp


def test_montar_bp_bate_ativo_com_passivo_mais_pl(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.04", conta_credito="2.1.01", valor=Decimal("2000.00"), historico="Compra de estoque a prazo"),
        Lancamento(data=date(2026, 1, 10), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("1000.00"), historico="Compra de imobilizado à vista"),
    ])
    db_session.commit()

    bp = montar_bp(db_session)

    assert bp["total_ativo"] == 7000.00
    assert bp["total_passivo_pl"] == 7000.00
    assert bp["balanceado"] is True

    ativo_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Circulante")
    assert ativo_circulante["subtotal"] == 6000.00

    ativo_nao_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Não Circulante")
    assert ativo_nao_circulante["subtotal"] == 1000.00

    patrimonio_liquido = next(s for s in bp["passivo_pl"] if s["grupo"] == "Patrimônio Líquido")
    assert patrimonio_liquido["subtotal"] == 5000.00


def test_endpoint_bp(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-02", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 500.0},
    )
    assert resposta.status_code == 201

    resposta = client.get("/relatorios/bp")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["balanceado"] is True
    assert corpo["total_ativo"] == 500.0
