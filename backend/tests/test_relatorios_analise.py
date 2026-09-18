from decimal import Decimal
from datetime import date

import pytest

from app.models import Lancamento
from app.relatorios import montar_analise


def _indicador(analise, chave):
    for familia in analise["familias"]:
        for indicador in familia["indicadores"]:
            if indicador["chave"] == chave:
                return indicador
    raise AssertionError(f"indicador {chave} não encontrado")


def _cenario_simples(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("10000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.04", conta_credito="2.1.01", valor=Decimal("4000.00"), historico="Compra de estoque a prazo"),
        Lancamento(data=date(2026, 1, 8), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("6000.00"), historico="Compra de imobilizado à vista"),
        Lancamento(data=date(2026, 1, 15), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("5000.00"), historico="Venda a prazo"),
        Lancamento(data=date(2026, 1, 15), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("2000.00"), historico="Baixa de CMV"),
    ])
    db_session.commit()


def test_analise_traz_tres_familias_e_onze_indicadores(db_session):
    _cenario_simples(db_session)

    analise = montar_analise(db_session)

    assert [f["nome"] for f in analise["familias"]] == [
        "Liquidez",
        "Estrutura de Capital",
        "Rentabilidade",
    ]
    total = sum(len(f["indicadores"]) for f in analise["familias"])
    assert total == 11


def test_analise_calcula_liquidez(db_session):
    # AC = Caixa 4.000 + Clientes 5.000 + Estoques 2.000 = 11.000; PC = 4.000.
    _cenario_simples(db_session)

    analise = montar_analise(db_session)

    corrente = _indicador(analise, "liquidez_corrente")
    assert corrente["numerador_valor"] == 11000.00
    assert corrente["denominador_valor"] == 4000.00
    assert corrente["valor"] == 2.75
    assert corrente["formula"] == "Ativo Circulante / Passivo Circulante"
    assert corrente["direcao"] == "maior_melhor"
    assert corrente["formato"] == "indice"
    assert corrente["motivo"] is None
    assert corrente["nao_significativo"] is False

    seca = _indicador(analise, "liquidez_seca")
    assert seca["numerador_valor"] == 9000.00
    assert seca["valor"] == 2.25

    imediata = _indicador(analise, "liquidez_imediata")
    assert imediata["numerador_valor"] == 4000.00
    assert imediata["valor"] == 1.0


def test_analise_calcula_estrutura_e_rentabilidade(db_session):
    # ANC = 6.000; Ativo Total = 17.000; PC + PNC = 4.000;
    # PL = Capital 10.000 + resultado 3.000 = 13.000; Receita = 5.000; CMV = 2.000.
    _cenario_simples(db_session)

    analise = montar_analise(db_session)

    participacao = _indicador(analise, "participacao_capital_terceiros")
    assert participacao["valor"] == pytest.approx(4000.0 / 13000.0)
    assert participacao["formato"] == "percentual"
    assert participacao["direcao"] == "menor_melhor"

    composicao = _indicador(analise, "composicao_endividamento")
    assert composicao["valor"] == 1.0

    imobilizacao = _indicador(analise, "imobilizacao_pl")
    assert imobilizacao["valor"] == pytest.approx(6000.0 / 13000.0)

    margem_bruta = _indicador(analise, "margem_bruta")
    assert margem_bruta["numerador_valor"] == 3000.00
    assert margem_bruta["valor"] == pytest.approx(0.6)

    margem_liquida = _indicador(analise, "margem_liquida")
    assert margem_liquida["valor"] == pytest.approx(0.6)

    roa = _indicador(analise, "roa")
    assert roa["valor"] == pytest.approx(3000.0 / 17000.0)

    roe = _indicador(analise, "roe")
    assert roe["valor"] == pytest.approx(3000.0 / 13000.0)

    giro = _indicador(analise, "giro_ativo")
    assert giro["valor"] == pytest.approx(5000.0 / 17000.0)
    assert giro["formato"] == "vezes"
    assert "média" in giro["observacao"]


def test_analise_com_razao_vazio_devolve_todos_nulos(db_session):
    analise = montar_analise(db_session)

    indicadores = [i for f in analise["familias"] for i in f["indicadores"]]
    assert len(indicadores) == 11
    for indicador in indicadores:
        assert indicador["valor"] is None
        assert indicador["motivo"] is not None
        assert indicador["nao_significativo"] is False

    corrente = _indicador(analise, "liquidez_corrente")
    assert corrente["motivo"] == "Passivo Circulante é zero."
    assert corrente["numerador_valor"] == 0.0
    assert corrente["denominador_valor"] == 0.0


def test_analise_marca_nao_significativo_com_pl_negativo(db_session):
    # Mesmos lançamentos de lancamentos_casos_extremos.csv:
    # Ativo 3.500; PC 8.000; Receita 2.000; CMV -500; resultado -5.500; PL -4.500.
    db_session.add_all([
        Lancamento(data=date(2026, 10, 1), conta_debito="1.1.02", conta_credito="2.3.01", valor=Decimal("1000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 10, 5), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("2000.00"), historico="Venda a prazo"),
        Lancamento(data=date(2026, 10, 10), conta_debito="4.1.02", conta_credito="2.1.03", valor=Decimal("8000.00"), historico="Folha de pagamento"),
        Lancamento(data=date(2026, 10, 15), conta_debito="1.1.01", conta_credito="4.1.01", valor=Decimal("500.00"), historico="Estorno de CMV"),
    ])
    db_session.commit()

    analise = montar_analise(db_session)

    for chave in ["participacao_capital_terceiros", "imobilizacao_pl", "roe"]:
        indicador = _indicador(analise, chave)
        assert indicador["valor"] is None, chave
        assert indicador["nao_significativo"] is True, chave
        assert indicador["denominador_valor"] == -4500.00, chave
        assert "negativo" in indicador["motivo"], chave

    # Os que não dependem do PL continuam sendo calculados normalmente.
    corrente = _indicador(analise, "liquidez_corrente")
    assert corrente["valor"] == 0.4375
    assert corrente["denominador_valor"] == 8000.00

    margem_bruta = _indicador(analise, "margem_bruta")
    assert margem_bruta["numerador_valor"] == 2500.00
    assert margem_bruta["valor"] == 1.25

    roa = _indicador(analise, "roa")
    assert roa["valor"] == pytest.approx(-5500.0 / 3500.0)


def test_analise_marca_nao_significativo_com_receita_negativa(db_session):
    # Estorno de venda sem venda anterior: a Receita fica negativa (-500) e o
    # Ativo também. A regra de denominador negativo é geral, não uma lista de
    # indicadores — aqui ela precisa pegar margens, ROA e giro, que não têm PL
    # nenhum no denominador.
    db_session.add_all([
        Lancamento(data=date(2026, 3, 1), conta_debito="3.1.01", conta_credito="1.1.01", valor=Decimal("500.00"), historico="Estorno de venda"),
    ])
    db_session.commit()

    analise = montar_analise(db_session)

    for chave in [
        "participacao_capital_terceiros",
        "imobilizacao_pl",
        "margem_bruta",
        "margem_liquida",
        "roa",
        "roe",
        "giro_ativo",
    ]:
        indicador = _indicador(analise, chave)
        assert indicador["valor"] is None, chave
        assert indicador["nao_significativo"] is True, chave
        assert indicador["denominador_valor"] == -500.00, chave
        assert "negativo" in indicador["motivo"], chave

    # Denominador zero continua sendo o outro caso, com a outra mensagem.
    corrente = _indicador(analise, "liquidez_corrente")
    assert corrente["valor"] is None
    assert corrente["nao_significativo"] is False
    assert corrente["motivo"] == "Passivo Circulante é zero."


def test_endpoint_analise(client):
    client.post("/lancamentos", json={"data": "2026-01-02", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 8000.0})
    client.post("/lancamentos", json={"data": "2026-01-05", "conta_debito": "1.1.04", "conta_credito": "2.1.01", "valor": 2000.0})

    resposta = client.get("/relatorios/analise")
    assert resposta.status_code == 200
    corpo = resposta.json()

    assert [f["nome"] for f in corpo["familias"]] == [
        "Liquidez",
        "Estrutura de Capital",
        "Rentabilidade",
    ]

    # AC = Caixa 8.000 + Estoques 2.000 = 10.000; PC = Fornecedores 2.000.
    corrente = _indicador(corpo, "liquidez_corrente")
    assert corrente["valor"] == 5.0
    assert corrente["numerador_valor"] == 10000.0
    assert corrente["denominador_valor"] == 2000.0

    # Sem receita no período, a margem bruta não pode ser calculada.
    margem_bruta = _indicador(corpo, "margem_bruta")
    assert margem_bruta["valor"] is None
    assert margem_bruta["motivo"] == "Receita é zero."
