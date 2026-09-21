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


def test_endpoint_bp_com_data_corte(client):
    client.post(
        "/lancamentos",
        json={"data": "2026-01-02", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 500.0},
    )
    client.post(
        "/lancamentos",
        json={"data": "2026-02-10", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 300.0},
    )

    resposta = client.get("/relatorios/bp?data_corte=2026-01-31")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_ativo"] == 500.0
    assert corpo["total_passivo_pl"] == 500.0
    assert corpo["balanceado"] is True

    # Sem o parâmetro, o mesmo endpoint continua somando a base inteira.
    resposta = client.get("/relatorios/bp")
    assert resposta.status_code == 200
    assert resposta.json()["total_ativo"] == 800.0


def test_endpoint_bp_data_corte_invalida_retorna_422(client):
    resposta = client.get("/relatorios/bp?data_corte=31-01-2026")
    assert resposta.status_code == 422


def _forma_bp(bp):
    return [(secao["grupo"], [c["codigo"] for c in secao["contas"]]) for secao in bp["ativo"] + bp["passivo_pl"]]


def test_montar_bp_produz_mesma_forma_com_ou_sem_lancamentos_no_corte(db_session):
    # Comparacao.jsx pareia os dois períodos por índice, não por código: a
    # mesma sequência de seções e contas tem de sair sempre, inclusive quando
    # `data_corte` cai antes de qualquer lançamento — o único caso em que
    # calcular_balancete percorre o ramo `lanc_df.empty`.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00")),
        Lancamento(data=date(2026, 2, 5), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("1000.00")),
        Lancamento(data=date(2026, 3, 10), conta_debito="1.1.04", conta_credito="2.1.01", valor=Decimal("2000.00")),
    ])
    db_session.commit()

    bp_antes = montar_bp(db_session, data_corte=date(2025, 12, 31))
    bp_depois = montar_bp(db_session, data_corte=date(2099, 12, 31))
    bp_sem_corte = montar_bp(db_session)

    assert _forma_bp(bp_antes) == _forma_bp(bp_depois) == _forma_bp(bp_sem_corte)
