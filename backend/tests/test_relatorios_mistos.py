from decimal import Decimal
from datetime import date

from app.models import Lancamento
from app.relatorios import montar_bp, montar_dre


def test_bp_bate_mesmo_com_lancamentos_de_resultado(db_session):
    db_session.add_all([
        Lancamento(data=date(2026, 1, 2), conta_debito="1.1.01", conta_credito="2.3.01", valor=Decimal("5000.00"), historico="Integralização de capital"),
        Lancamento(data=date(2026, 1, 5), conta_debito="1.1.04", conta_credito="2.1.01", valor=Decimal("2000.00"), historico="Compra de estoque a prazo"),
        Lancamento(data=date(2026, 1, 10), conta_debito="1.2.01", conta_credito="1.1.01", valor=Decimal("1000.00"), historico="Compra de imobilizado à vista"),
        Lancamento(data=date(2026, 1, 15), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00"), historico="Venda a prazo"),
        Lancamento(data=date(2026, 1, 15), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00"), historico="Baixa de CMV"),
    ])
    db_session.commit()

    bp = montar_bp(db_session)
    dre = montar_dre(db_session)

    assert dre["resultado_periodo"] == 1800.00
    assert bp["total_ativo"] == 8800.00
    assert bp["total_passivo_pl"] == 8800.00
    assert bp["balanceado"] is True

    patrimonio_liquido = next(s for s in bp["passivo_pl"] if s["grupo"] == "Patrimônio Líquido")
    linha_resultado = next(c for c in patrimonio_liquido["contas"] if c["codigo"] == "RESULTADO")
    assert linha_resultado["saldo"] == 1800.00
