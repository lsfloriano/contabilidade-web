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


def test_montar_bp_com_data_corte_soma_ate_a_data_inclusive(db_session):
    db_session.add_all([
        # Antes do corte.
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00"), historico="Integralização de capital"),
        # Exatamente na data de corte: entra.
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.04", conta_credito="2.1.01", valor=Decimal("2000.00"), historico="Compra de estoque a prazo"),
        # Depois do corte: fica de fora.
        Lancamento(data=date(2026, 2, 5), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("1000.00"), historico="Compra de imobilizado à vista"),
    ])
    db_session.commit()

    bp = montar_bp(db_session, data_corte=date(2026, 1, 31))

    ativo_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Circulante")
    assert ativo_circulante["subtotal"] == 7000.00  # Caixa 5000 + Estoques 2000

    ativo_nao_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Não Circulante")
    assert ativo_nao_circulante["subtotal"] == 0.00  # imobilizado só em fevereiro

    assert bp["total_ativo"] == 7000.00
    assert bp["total_passivo_pl"] == 7000.00  # Fornecedores 2000 + PL 5000
    # A equação patrimonial fecha para qualquer corte de data, não só para a
    # base inteira: é a mesma invariante de partida dobrada.
    assert bp["balanceado"] is True


def test_montar_bp_sem_data_corte_inclui_lancamento_futuro(db_session):
    # Regressão: sem data_corte nada é filtrado — em particular, não existe um
    # corte implícito em "hoje".
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00")),
        Lancamento(data=date(2099, 12, 31), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("100.00")),
    ])
    db_session.commit()

    bp = montar_bp(db_session)

    ativo_circulante = next(s for s in bp["ativo"] if s["grupo"] == "Ativo Circulante")
    assert ativo_circulante["subtotal"] == 5100.00
    assert bp["total_ativo"] == 5100.00
    assert bp["total_passivo_pl"] == 5100.00
    assert bp["balanceado"] is True


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
