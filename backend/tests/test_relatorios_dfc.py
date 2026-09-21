from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import (
    CONTAS_CAIXA,
    _categoria_dfc,
    _contas_dataframe,
    calcular_balancete,
    montar_dfc,
)


def test_categoria_dfc_classifica_todas_as_contas_do_plano(db_session):
    # Caixa (1.1.01) e Bancos (1.1.02) ficam de fora: nunca são contraparte de
    # um movimento de caixa, então a categoria que _categoria_dfc devolveria
    # para elas não significa nada. A união com CONTAS_CAIXA é o que prova que
    # o plano de contas inteiro (20 contas de seed.py) está coberto — se uma
    # conta nova for semeada um dia, este teste cai e alguém decide a
    # atividade dela de propósito.
    esperado = {
        "1.1.03": "operacional",     # Clientes
        "1.1.04": "operacional",     # Estoques
        "1.2.01": "investimento",    # Imobilizado
        "1.2.02": "investimento",    # Investimentos
        "2.1.01": "operacional",     # Fornecedores
        "2.1.02": "financiamento",   # Empréstimos CP (exceção por código)
        "2.1.03": "operacional",     # Salários a Pagar
        "2.1.04": "operacional",     # Impostos a Pagar
        "2.2.01": "financiamento",   # Empréstimos LP (exceção por código)
        "2.3.01": "financiamento",   # Capital Social
        "2.3.02": "financiamento",   # Lucros/Prejuízos Acumulados
        "3.1.01": "operacional",     # Receita de Vendas
        "3.1.02": "operacional",     # Receita de Serviços
        "4.1.01": "operacional",     # CMV
        "4.1.02": "operacional",     # Despesas Administrativas
        "4.1.03": "operacional",     # Despesas com Vendas
        "4.1.04": "operacional",     # Despesas Financeiras (juros como
                                     # operacional é a prática brasileira usual)
        "4.1.05": "operacional",     # Impostos sobre Vendas
    }

    contas = {c["codigo"]: c for c in _contas_dataframe(db_session).to_dict("records")}
    assert set(esperado) | CONTAS_CAIXA == set(contas)

    for codigo, categoria in esperado.items():
        assert _categoria_dfc(contas[codigo]) == categoria, codigo


def test_montar_dfc_classifica_as_tres_atividades_com_sinal(db_session):
    db_session.add_all([
        # Entrada operacional: recebimento de venda à vista.
        Lancamento(data=date(2026, 1, 3), conta_debito="1.1.01", conta_credito="3.1.01", valor=Decimal("3000.00"), historico="Venda à vista"),
        # Saída operacional: despesa paga pelo banco.
        Lancamento(data=date(2026, 1, 4), conta_debito="4.1.02", conta_credito="1.1.02", valor=Decimal("500.00"), historico="Aluguel"),
        # Saída de investimento: compra de imobilizado à vista.
        Lancamento(data=date(2026, 1, 5), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("1000.00"), historico="Compra de máquina"),
        # Entrada de financiamento: empréstimo captado (exceção por código —
        # 2.1.02 é Passivo Circulante, mas é financiamento).
        Lancamento(data=date(2026, 1, 6), conta_debito="1.1.02", conta_credito="2.1.02", valor=Decimal("2000.00"), historico="Empréstimo captado"),
        # Entrada de financiamento: integralização de capital.
        Lancamento(data=date(2026, 1, 7), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00"), historico="Integralização de capital"),
    ])
    db_session.commit()

    dfc = montar_dfc(db_session)

    # Operacional: +3000 (Receita de Vendas) −500 (Despesas Administrativas).
    assert dfc["subtotal_operacionais"] == 2500.00
    receita_vendas = next(l for l in dfc["operacionais"] if l["codigo"] == "3.1.01")
    assert receita_vendas["nome"] == "Receita de Vendas"
    assert receita_vendas["valor"] == 3000.00
    administrativas = next(l for l in dfc["operacionais"] if l["codigo"] == "4.1.02")
    assert administrativas["valor"] == -500.00

    # Investimento: −1000 (Imobilizado).
    assert dfc["subtotal_investimentos"] == -1000.00
    imobilizado = next(l for l in dfc["investimentos"] if l["codigo"] == "1.2.01")
    assert imobilizado["nome"] == "Imobilizado"
    assert imobilizado["valor"] == -1000.00

    # Financiamento: +2000 (Empréstimos CP) +5000 (Capital Social).
    assert dfc["subtotal_financiamentos"] == 7000.00
    emprestimos_cp = next(l for l in dfc["financiamentos"] if l["codigo"] == "2.1.02")
    assert emprestimos_cp["nome"] == "Empréstimos CP"
    assert emprestimos_cp["valor"] == 2000.00
    capital = next(l for l in dfc["financiamentos"] if l["codigo"] == "2.3.01")
    assert capital["valor"] == 5000.00

    # 2500 − 1000 + 7000 = 8500. Caixa: +3000 +5000 −1000 = 7000;
    # Bancos: +2000 −500 = 1500; soma 8500.
    assert dfc["variacao_liquida"] == 8500.00
    assert dfc["saldo_inicial"] == 0.0
    assert dfc["saldo_final"] == 8500.00
    assert dfc["confere"] is True

    # Caixa e Bancos nunca são linha do relatório — são as pontas que definem
    # o que é caixa.
    codigos = [
        l["codigo"]
        for l in dfc["operacionais"] + dfc["investimentos"] + dfc["financiamentos"]
    ]
    assert "1.1.01" not in codigos
    assert "1.1.02" not in codigos


def test_montar_dfc_exclui_transferencia_entre_caixa_e_bancos(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 3), conta_debito="1.1.01", conta_credito="3.1.01", valor=Decimal("1000.00"), historico="Venda à vista"),
        # Os dois lados são caixa: transferência interna, não é entrada nem
        # saída real de caixa.
        Lancamento(data=date(2026, 1, 4), conta_debito="1.1.02", conta_credito="1.1.01", valor=Decimal("800.00"), historico="Depósito em banco"),
    ])
    db_session.commit()

    dfc = montar_dfc(db_session)

    # Só a venda entra: +1000 operacional. A transferência não cria linha
    # nenhuma em nenhuma das três atividades.
    assert dfc["subtotal_operacionais"] == 1000.00
    assert len(dfc["operacionais"]) == 1
    assert dfc["investimentos"] == []
    assert dfc["financiamentos"] == []
    assert dfc["variacao_liquida"] == 1000.00

    # E o fechamento continua valendo: Caixa +1000 −800 = 200,
    # Bancos +800 = 800, soma 1000 — a transferência se cancela na soma
    # Caixa+Bancos, que é exatamente por que excluí-la não muda o total.
    assert dfc["saldo_final"] == 1000.00
    assert dfc["confere"] is True


def test_montar_dfc_exclui_lancamento_sem_lado_em_caixa(db_session):
    db_session.add_all([
        # Venda a prazo: nenhum lado é caixa. Ainda não é fluxo de caixa.
        Lancamento(data=date(2026, 1, 3), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("4000.00"), historico="Venda a prazo"),
        # O recebimento, sim, é fluxo de caixa — e a contraparte é Clientes,
        # não Receita de Vendas.
        Lancamento(data=date(2026, 2, 10), conta_debito="1.1.01", conta_credito="1.1.03", valor=Decimal("4000.00"), historico="Recebimento de cliente"),
    ])
    db_session.commit()

    dfc = montar_dfc(db_session)

    assert len(dfc["operacionais"]) == 1
    clientes = dfc["operacionais"][0]
    assert clientes["codigo"] == "1.1.03"
    assert clientes["nome"] == "Clientes"
    assert clientes["valor"] == 4000.00
    # A receita não aparece na DFC: ela já foi reconhecida na DRE quando a
    # venda a prazo foi lançada, e o caixa só se move no recebimento.
    assert all(l["codigo"] != "3.1.01" for l in dfc["operacionais"])

    # Caixa +4000; Clientes +4000 −4000 = 0 (e não é conta de caixa).
    assert dfc["variacao_liquida"] == 4000.00
    assert dfc["saldo_final"] == 4000.00
    assert dfc["confere"] is True


def test_montar_dfc_agrupa_lancamentos_da_mesma_conta_numa_linha(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 10), conta_debito="4.1.02", conta_credito="1.1.01", valor=Decimal("300.00"), historico="Material de escritório"),
        Lancamento(data=date(2026, 1, 20), conta_debito="4.1.02", conta_credito="1.1.02", valor=Decimal("200.00"), historico="Energia elétrica"),
    ])
    db_session.commit()

    dfc = montar_dfc(db_session)

    # Uma linha por conta, somando os lançamentos daquela conta — mesmo estilo
    # do Balancete/DRE, nunca lançamento a lançamento. Duas saídas pela mesma
    # conta, por caixas diferentes, viram −500 numa linha só.
    assert len(dfc["operacionais"]) == 1
    assert dfc["operacionais"][0]["codigo"] == "4.1.02"
    assert dfc["operacionais"][0]["valor"] == -500.00
    assert dfc["subtotal_operacionais"] == -500.00

    # Caixa −300, Bancos −200: caixa negativo é possível nesta base e o
    # fechamento tem de valer para ele também.
    assert dfc["saldo_final"] == -500.00
    assert dfc["confere"] is True


def test_montar_dfc_sem_lancamentos(db_session):
    dfc = montar_dfc(db_session)

    assert dfc["operacionais"] == []
    assert dfc["investimentos"] == []
    assert dfc["financiamentos"] == []
    assert dfc["subtotal_operacionais"] == 0.0
    assert dfc["subtotal_investimentos"] == 0.0
    assert dfc["subtotal_financiamentos"] == 0.0
    assert dfc["variacao_liquida"] == 0.0
    assert dfc["saldo_inicial"] == 0.0
    assert dfc["saldo_final"] == 0.0
    assert dfc["confere"] is True


def test_montar_dfc_fecha_com_saldo_de_caixa_e_bancos_do_balancete(db_session):
    # O teste formal do fechamento, com lançamentos cobrindo as três
    # atividades, mais uma transferência interna e um lançamento sem lado em
    # caixa (os dois casos excluídos). São dois caminhos de cálculo
    # independentes — montar_dfc itera os lançamentos brutos, calcular_balancete
    # agrupa por conta — chegando ao mesmo número.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("10000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 3), conta_debito="1.1.02", conta_credito="2.2.01", valor=Decimal("5000.00"), historico="Empréstimo de longo prazo"),
        Lancamento(data=date(2026, 1, 4), conta_debito="1.2.01", conta_credito="1.1.02", valor=Decimal("4000.00"), historico="Compra de imobilizado"),
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.01", conta_credito="3.1.02", valor=Decimal("2500.00"), historico="Serviço prestado à vista"),
        Lancamento(data=date(2026, 1, 6), conta_debito="4.1.03", conta_credito="1.1.01", valor=Decimal("700.00"), historico="Comissão de vendas"),
        Lancamento(data=date(2026, 1, 7), conta_debito="2.1.01", conta_credito="1.1.02", valor=Decimal("1300.00"), historico="Pagamento a fornecedor"),
        # Excluído: transferência interna.
        Lancamento(data=date(2026, 1, 8), conta_debito="1.1.02", conta_credito="1.1.01", valor=Decimal("3000.00"), historico="Depósito em banco"),
        # Excluído: nenhum lado é caixa.
        Lancamento(data=date(2026, 1, 9), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("6000.00"), historico="Venda a prazo"),
        Lancamento(data=date(2026, 1, 10), conta_debito="4.1.04", conta_credito="1.1.02", valor=Decimal("250.00"), historico="Juros do empréstimo"),
    ])
    db_session.commit()

    dfc = montar_dfc(db_session)

    # Operacional: +2500 (Receita de Serviços) −700 (Despesas com Vendas)
    #              −1300 (Fornecedores) −250 (Despesas Financeiras) = 250.
    assert dfc["subtotal_operacionais"] == 250.00
    # Investimento: −4000 (Imobilizado).
    assert dfc["subtotal_investimentos"] == -4000.00
    # Financiamento: +10000 (Capital Social) +5000 (Empréstimos LP) = 15000.
    assert dfc["subtotal_financiamentos"] == 15000.00
    # 250 − 4000 + 15000 = 11250.
    assert dfc["variacao_liquida"] == 11250.00
    assert dfc["saldo_final"] == 11250.00

    # Pelo outro caminho: Caixa (devedora) débitos 10000 + 2500 = 12500,
    # créditos 700 + 3000 = 3700, saldo 8800. Bancos (devedora) débitos
    # 5000 + 3000 = 8000, créditos 4000 + 1300 + 250 = 5550, saldo 2450.
    # 8800 + 2450 = 11250.
    balancete = calcular_balancete(db_session)
    saldo_caixa_bancos = sum(c["saldo"] for c in balancete if c["codigo"] in CONTAS_CAIXA)
    assert saldo_caixa_bancos == 11250.00

    assert dfc["saldo_final"] == saldo_caixa_bancos
    assert dfc["confere"] is True
