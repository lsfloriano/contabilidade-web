from datetime import date
from io import BytesIO

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Lancamento, ContaContabil, Natureza, Grupo, TipoConta


def _lancamentos_dataframe(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> pd.DataFrame:
    """Lançamentos como DataFrame, opcionalmente recortados por data.

    O filtro é aplicado na consulta, não no DataFrame: com os dois parâmetros
    `None` — o padrão, e o que as quatro páginas existentes usam — a consulta é
    exatamente a de antes e o DataFrame sai idêntico, inclusive nas colunas
    (nenhuma coluna `data` é acrescentada).
    """
    consulta = db.query(Lancamento)
    if data_inicio is not None:
        consulta = consulta.filter(Lancamento.data >= data_inicio)
    if data_fim is not None:
        consulta = consulta.filter(Lancamento.data <= data_fim)
    lancamentos = consulta.all()
    rows = [
        {"conta_debito": l.conta_debito, "conta_credito": l.conta_credito, "valor": float(l.valor)}
        for l in lancamentos
    ]
    return pd.DataFrame(rows, columns=["conta_debito", "conta_credito", "valor"])


def _contas_dataframe(db: Session) -> pd.DataFrame:
    contas = db.query(ContaContabil).order_by(ContaContabil.codigo).all()
    return pd.DataFrame([
        {
            "codigo": c.codigo,
            "nome": c.nome,
            "natureza": c.natureza.value,
            "grupo": c.grupo.value,
            "tipo": c.tipo.value,
        }
        for c in contas
    ])


def calcular_balancete(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[dict]:
    lanc_df = _lancamentos_dataframe(db, data_inicio=data_inicio, data_fim=data_fim)
    contas_df = _contas_dataframe(db)

    if lanc_df.empty:
        debitos = pd.Series(dtype=float)
        creditos = pd.Series(dtype=float)
    else:
        debitos = lanc_df.groupby("conta_debito")["valor"].sum()
        creditos = lanc_df.groupby("conta_credito")["valor"].sum()

    resultado = []
    for _, conta in contas_df.iterrows():
        total_debito = float(debitos.get(conta["codigo"], 0.0))
        total_credito = float(creditos.get(conta["codigo"], 0.0))

        if conta["natureza"] == Natureza.devedora.value:
            saldo = total_debito - total_credito
        else:
            saldo = total_credito - total_debito

        resultado.append({
            "codigo": conta["codigo"],
            "nome": conta["nome"],
            "grupo": conta["grupo"],
            "tipo": conta["tipo"],
            "total_debito": total_debito,
            "total_credito": total_credito,
            "saldo": saldo,
        })
    return resultado


def montar_balancete(db: Session) -> dict:
    # Toda linha de calcular_balancete fica igual — isso aqui só soma as duas
    # colunas de dinheiro. Por partida dobrada, cada lançamento credita uma
    # conta e debita outra pelo mesmo valor, então as somas SEMPRE fecham
    # iguais; é a prova de que o balancete existe para mostrar. O frontend
    # exibe a diferença via classeValor — se um dia vier diferente de zero,
    # é bug de dados, não de arredondamento (ambas somam floats crus, igual
    # ao resto do app).
    linhas = calcular_balancete(db)
    return {
        "linhas": linhas,
        "total_debito": sum(linha["total_debito"] for linha in linhas),
        "total_credito": sum(linha["total_credito"] for linha in linhas),
    }


def montar_balancete_planilha(db: Session) -> pd.DataFrame:
    # Espelha a tabela da página: "código - nome" numa coluna só, mais a
    # linha de Total que já existe na tela (grupo em branco, saldo é a
    # diferença entre os dois totais, igual ao que Balancete.jsx calcula).
    balancete = montar_balancete(db)
    linhas = [
        {
            "Conta": f"{linha['codigo']} - {linha['nome']}",
            "Grupo": linha["grupo"],
            "Total débito": linha["total_debito"],
            "Total crédito": linha["total_credito"],
            "Saldo": linha["saldo"],
        }
        for linha in balancete["linhas"]
    ]
    linhas.append({
        "Conta": "Total",
        "Grupo": "",
        "Total débito": balancete["total_debito"],
        "Total crédito": balancete["total_credito"],
        "Saldo": balancete["total_debito"] - balancete["total_credito"],
    })
    return pd.DataFrame(
        linhas, columns=["Conta", "Grupo", "Total débito", "Total crédito", "Saldo"]
    )


GRUPOS_ATIVO = [Grupo.ativo_circulante.value, Grupo.ativo_nao_circulante.value]
GRUPOS_PASSIVO_PL = [Grupo.passivo_circulante.value, Grupo.passivo_nao_circulante.value, Grupo.patrimonio_liquido.value]


def _agrupar_secoes(contas: list[dict], grupos: list[str]) -> tuple[list[dict], float]:
    secoes = []
    total = 0.0
    for grupo in grupos:
        contas_grupo = [c for c in contas if c["grupo"] == grupo]
        subtotal = sum(c["saldo"] for c in contas_grupo)
        total += subtotal
        secoes.append({
            "grupo": grupo,
            "contas": [{"codigo": c["codigo"], "nome": c["nome"], "saldo": c["saldo"]} for c in contas_grupo],
            "subtotal": subtotal,
        })
    return secoes, total


def montar_bp(db: Session, data_corte: date | None = None) -> dict:
    # BP é foto: acumula desde o primeiro lançamento até `data_corte`, que por
    # isso entra como `data_fim` e não tem contraparte de início.
    balancete = calcular_balancete(db, data_fim=data_corte)
    patrimoniais = [c for c in balancete if c["tipo"] == TipoConta.patrimonial.value]
    resultado = [c for c in balancete if c["tipo"] == TipoConta.resultado.value]

    ativo_secoes, total_ativo = _agrupar_secoes(patrimoniais, GRUPOS_ATIVO)
    passivo_pl_secoes, total_passivo_pl = _agrupar_secoes(patrimoniais, GRUPOS_PASSIVO_PL)

    total_receitas = sum(c["saldo"] for c in resultado if c["grupo"] == Grupo.receita.value)
    total_despesas = sum(c["saldo"] for c in resultado if c["grupo"] == Grupo.despesa.value)
    resultado_periodo = total_receitas - total_despesas

    patrimonio_liquido = next(s for s in passivo_pl_secoes if s["grupo"] == Grupo.patrimonio_liquido.value)
    patrimonio_liquido["contas"].append({
        "codigo": "RESULTADO",
        "nome": "Resultado do Exercício (não realizado)",
        "saldo": resultado_periodo,
    })
    patrimonio_liquido["subtotal"] += resultado_periodo
    total_passivo_pl += resultado_periodo

    return {
        "ativo": ativo_secoes,
        "passivo_pl": passivo_pl_secoes,
        "total_ativo": total_ativo,
        "total_passivo_pl": total_passivo_pl,
        "balanceado": abs(total_ativo - total_passivo_pl) < 0.01,
    }


def montar_bp_planilha(db: Session, data_corte: date | None = None) -> pd.DataFrame:
    # Formato longo (uma linha por conta, mais subtotal e total), não um
    # espelho visual das duas colunas da tela: uma planilha achatada é o que
    # se abre e já dá pra somar/dinamizar, ao contrário de tentar recriar a
    # conta T num layout de duas colunas dentro de uma aba só.
    bp = montar_bp(db, data_corte=data_corte)
    linhas = []
    for lado, secoes, total in (
        ("Ativo", bp["ativo"], bp["total_ativo"]),
        ("Passivo + Patrimônio Líquido", bp["passivo_pl"], bp["total_passivo_pl"]),
    ):
        for secao in secoes:
            for conta in secao["contas"]:
                linhas.append({
                    "Lado": lado,
                    "Grupo": secao["grupo"],
                    "Conta": conta["nome"],
                    "Saldo": conta["saldo"],
                })
            linhas.append({
                "Lado": lado,
                "Grupo": secao["grupo"],
                "Conta": "Subtotal",
                "Saldo": secao["subtotal"],
            })
        linhas.append({"Lado": lado, "Grupo": "", "Conta": "Total", "Saldo": total})
    return pd.DataFrame(linhas, columns=["Lado", "Grupo", "Conta", "Saldo"])


def montar_dre(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> dict:
    # DRE é fluxo: só o que ocorreu dentro do intervalo. Sem os parâmetros, o
    # comportamento de hoje continua — período contínuo único, desde o início.
    balancete = calcular_balancete(db, data_inicio=data_inicio, data_fim=data_fim)
    resultado_contas = [c for c in balancete if c["tipo"] == TipoConta.resultado.value]

    receitas = [c for c in resultado_contas if c["grupo"] == Grupo.receita.value]
    despesas = [c for c in resultado_contas if c["grupo"] == Grupo.despesa.value]

    total_receitas = sum(c["saldo"] for c in receitas)
    total_despesas = sum(c["saldo"] for c in despesas)

    return {
        "receitas": [{"codigo": c["codigo"], "nome": c["nome"], "valor": c["saldo"]} for c in receitas],
        "despesas": [{"codigo": c["codigo"], "nome": c["nome"], "valor": c["saldo"]} for c in despesas],
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_periodo": total_receitas - total_despesas,
    }


def montar_dre_planilha(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> pd.DataFrame:
    dre = montar_dre(db, data_inicio=data_inicio, data_fim=data_fim)
    linhas = []
    for tipo, contas, total, rotulo_total in (
        ("Receita", dre["receitas"], dre["total_receitas"], "Total de receitas"),
        ("Despesa", dre["despesas"], dre["total_despesas"], "Total de despesas"),
    ):
        for conta in contas:
            linhas.append({"Tipo": tipo, "Conta": conta["nome"], "Valor": conta["valor"]})
        linhas.append({"Tipo": tipo, "Conta": rotulo_total, "Valor": total})
    linhas.append({
        "Tipo": "Resultado",
        "Conta": "Resultado do período",
        "Valor": dre["resultado_periodo"],
    })
    return pd.DataFrame(linhas, columns=["Tipo", "Conta", "Valor"])


CODIGO_CAIXA = "1.1.01"
CODIGO_BANCOS = "1.1.02"
CODIGO_ESTOQUES = "1.1.04"
CODIGO_CMV = "4.1.01"

DIRECAO_MAIOR = "maior_melhor"
DIRECAO_MENOR = "menor_melhor"

FORMATO_INDICE = "indice"
FORMATO_PERCENTUAL = "percentual"
FORMATO_VEZES = "vezes"


def _formatar_pt_br(valor: float) -> str:
    """Formata um número no padrão pt-BR (milhar '.', decimal ','), o mesmo
    formato que `fmt` produz no frontend (graficos-comuns.js), para que um
    valor citado em texto no backend não destoe dos números da tabela."""
    texto = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sinal = "-" if valor < 0 else ""
    return f"{sinal}{texto}"


def _indicador(
    chave: str,
    nome: str,
    formula: str,
    numerador_nome: str,
    numerador_valor: float,
    denominador_nome: str,
    denominador_valor: float,
    direcao: str,
    formato: str,
    observacao: str | None = None,
) -> dict:
    """Monta um indicador já resolvido.

    Divisão por zero aqui é rotina (empresa sem passivo circulante, razão
    vazio), não exceção: devolve valor None e o motivo.

    Denominador negativo produz um quociente definido mas financeiramente
    enganoso: prejuízo dividido por PL negativo vira número positivo e é lido
    como retorno; receita negativa faz o mesmo com as margens. A regra vale para
    qualquer indicador, não para uma lista deles — é uma checagem sobre o
    denominador, e é por isso que não existe flag por indicador aqui.
    """
    valor = None
    motivo = None
    nao_significativo = False

    if denominador_valor == 0:
        motivo = f"{denominador_nome} é zero."
    elif denominador_valor < 0:
        nao_significativo = True
        motivo = (
            f"{denominador_nome} é negativo. O quociente existe, mas muda de "
            "sinal e seria lido como se a situação fosse melhor do que é. O "
            "indicador não é significativo neste caso; use o Balanço "
            "Patrimonial e a DRE."
        )
    else:
        valor = numerador_valor / denominador_valor

    return {
        "chave": chave,
        "nome": nome,
        "valor": valor,
        "formula": formula,
        "numerador_nome": numerador_nome,
        "numerador_valor": numerador_valor,
        "denominador_nome": denominador_nome,
        "denominador_valor": denominador_valor,
        "direcao": direcao,
        "formato": formato,
        "motivo": motivo,
        "nao_significativo": nao_significativo,
        "observacao": observacao,
    }


def montar_analise(db: Session) -> dict:
    balancete = calcular_balancete(db)
    saldos = {c["codigo"]: c["saldo"] for c in balancete}
    patrimoniais = [c for c in balancete if c["tipo"] == TipoConta.patrimonial.value]

    def subtotal(grupo: str) -> float:
        return sum(c["saldo"] for c in patrimoniais if c["grupo"] == grupo)

    dre = montar_dre(db)
    receita = dre["total_receitas"]
    resultado = dre["resultado_periodo"]

    ativo_circulante = subtotal(Grupo.ativo_circulante.value)
    ativo_nao_circulante = subtotal(Grupo.ativo_nao_circulante.value)
    passivo_circulante = subtotal(Grupo.passivo_circulante.value)
    passivo_nao_circulante = subtotal(Grupo.passivo_nao_circulante.value)
    # O PL do período inclui o resultado ainda não realizado, igual ao montar_bp.
    # Isto não é opcional: sem somar o resultado, o denominador do ROE
    # contradiria o Patrimônio Líquido que o usuário lê na aba do Balanço
    # Patrimonial. Duas páginas discordando da mesma cifra é o tipo de
    # inconsistência silenciosa que destrói a confiança numa ferramenta de
    # ensino. Não "conserte" isto.
    patrimonio_liquido = subtotal(Grupo.patrimonio_liquido.value) + resultado

    ativo_total = ativo_circulante + ativo_nao_circulante
    capital_terceiros = passivo_circulante + passivo_nao_circulante
    estoques = saldos.get(CODIGO_ESTOQUES, 0.0)
    disponivel = saldos.get(CODIGO_CAIXA, 0.0) + saldos.get(CODIGO_BANCOS, 0.0)
    cmv = saldos.get(CODIGO_CMV, 0.0)

    margem_bruta_observacao = (
        "Usa a receita bruta. Nesta aplicação, Impostos sobre Vendas é "
        "classificado como despesa, então não existe receita líquida "
        "separada — a margem clássica usa a receita líquida de vendas. A "
        "receita também inclui Receita de Serviços, que não tem CMV."
    )
    if cmv < 0:
        # Mesma causa raiz do aviso de GraficoDRE ("CMV negativa não pode ser
        # representada na cascata"), mas aqui o CMV nem aparece na linha de
        # substituição — sem isto, uma margem acima de 100% fica sem explicação
        # nesta página.
        margem_bruta_observacao += (
            f" O CMV do período é negativo ({_formatar_pt_br(cmv)}), o que "
            "eleva a margem acima de 100%; verifique estornos em Lançamentos."
        )

    liquidez = [
        _indicador(
            chave="liquidez_corrente",
            nome="Liquidez Corrente",
            formula="Ativo Circulante / Passivo Circulante",
            numerador_nome="Ativo Circulante",
            numerador_valor=ativo_circulante,
            denominador_nome="Passivo Circulante",
            denominador_valor=passivo_circulante,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_INDICE,
        ),
        # A forma completa de Marion também subtrai despesas antecipadas do
        # numerador. `seed.py` não tem conta de despesas antecipadas, então
        # aqui a fórmula reduzida coincide com a completa — mas isso é uma
        # propriedade deste plano de contas hoje, não uma definição.
        _indicador(
            chave="liquidez_seca",
            nome="Liquidez Seca",
            formula="(Ativo Circulante − Estoques) / Passivo Circulante",
            numerador_nome="Ativo Circulante − Estoques",
            numerador_valor=ativo_circulante - estoques,
            denominador_nome="Passivo Circulante",
            denominador_valor=passivo_circulante,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_INDICE,
        ),
        _indicador(
            chave="liquidez_imediata",
            nome="Liquidez Imediata",
            formula="(Caixa + Bancos) / Passivo Circulante",
            numerador_nome="Caixa + Bancos",
            numerador_valor=disponivel,
            denominador_nome="Passivo Circulante",
            denominador_valor=passivo_circulante,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_INDICE,
        ),
    ]

    estrutura = [
        _indicador(
            chave="participacao_capital_terceiros",
            nome="Participação de Capital de Terceiros",
            formula="(Passivo Circulante + Passivo Não Circulante) / Patrimônio Líquido",
            numerador_nome="Passivo Circulante + Passivo Não Circulante",
            numerador_valor=capital_terceiros,
            denominador_nome="Patrimônio Líquido",
            denominador_valor=patrimonio_liquido,
            direcao=DIRECAO_MENOR,
            formato=FORMATO_PERCENTUAL,
        ),
        _indicador(
            chave="composicao_endividamento",
            nome="Composição do Endividamento",
            formula="Passivo Circulante / (Passivo Circulante + Passivo Não Circulante)",
            numerador_nome="Passivo Circulante",
            numerador_valor=passivo_circulante,
            denominador_nome="Passivo Circulante + Passivo Não Circulante",
            denominador_valor=capital_terceiros,
            direcao=DIRECAO_MENOR,
            formato=FORMATO_PERCENTUAL,
        ),
        # A fórmula clássica é (Investimentos + Imobilizado + Intangível) / PL.
        # Usamos Ativo Não Circulante porque este plano de contas não tem uma
        # conta de Realizável a Longo Prazo — então ANC e a soma clássica
        # coincidem hoje. No dia em que uma conta de ARLP for semeada, este
        # `formula` deixa de ser uma definição correta e precisa mudar junto.
        _indicador(
            chave="imobilizacao_pl",
            nome="Imobilização do Patrimônio Líquido",
            formula="Ativo Não Circulante / Patrimônio Líquido",
            numerador_nome="Ativo Não Circulante",
            numerador_valor=ativo_nao_circulante,
            denominador_nome="Patrimônio Líquido",
            denominador_valor=patrimonio_liquido,
            direcao=DIRECAO_MENOR,
            formato=FORMATO_PERCENTUAL,
        ),
    ]

    rentabilidade = [
        _indicador(
            chave="margem_bruta",
            nome="Margem Bruta",
            formula="(Receita − CMV) / Receita",
            numerador_nome="Receita − CMV",
            numerador_valor=receita - cmv,
            denominador_nome="Receita",
            denominador_valor=receita,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_PERCENTUAL,
            observacao=margem_bruta_observacao,
        ),
        _indicador(
            chave="margem_liquida",
            nome="Margem Líquida",
            formula="Resultado do Período / Receita",
            numerador_nome="Resultado do Período",
            numerador_valor=resultado,
            denominador_nome="Receita",
            denominador_valor=receita,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_PERCENTUAL,
            observacao=(
                "Usa a receita bruta. Nesta aplicação, Impostos sobre Vendas é "
                "classificado como despesa, então não existe receita líquida "
                "separada — a margem clássica usa a receita líquida de vendas."
            ),
        ),
        _indicador(
            chave="roa",
            nome="ROA — Retorno sobre o Ativo",
            formula="Resultado do Período / Ativo Total",
            numerador_nome="Resultado do Período",
            numerador_valor=resultado,
            denominador_nome="Ativo Total",
            denominador_valor=ativo_total,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_PERCENTUAL,
            observacao=(
                "Usa o saldo final do Ativo, não a média do período que a "
                "fórmula clássica pede. Esta aplicação trabalha com um período "
                "contínuo único."
            ),
        ),
        _indicador(
            chave="roe",
            nome="ROE — Retorno sobre o Patrimônio Líquido",
            formula="Resultado do Período / Patrimônio Líquido",
            numerador_nome="Resultado do Período",
            numerador_valor=resultado,
            denominador_nome="Patrimônio Líquido",
            denominador_valor=patrimonio_liquido,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_PERCENTUAL,
            observacao=(
                "Usa o saldo final do Patrimônio Líquido, não a média do "
                "período. Além disso, o PL aqui já inclui o resultado do "
                "período — mesmo critério do Balanço Patrimonial, para as duas "
                "páginas não divergirem —, de modo que o numerador está contido "
                "no denominador. A fórmula clássica usa o PL inicial ou médio "
                "justamente para evitar isso."
            ),
        ),
        _indicador(
            chave="giro_ativo",
            nome="Giro do Ativo",
            formula="Receita / Ativo Total",
            numerador_nome="Receita",
            numerador_valor=receita,
            denominador_nome="Ativo Total",
            denominador_valor=ativo_total,
            direcao=DIRECAO_MAIOR,
            formato=FORMATO_VEZES,
            observacao=(
                "Usa o Ativo Total do fim do período. A fórmula clássica usa a "
                "média do ativo entre dois períodos; este app trabalha com um "
                "único período contínuo."
            ),
        ),
    ]

    return {
        "familias": [
            {"nome": "Liquidez", "indicadores": liquidez},
            {"nome": "Estrutura de Capital", "indicadores": estrutura},
            {"nome": "Rentabilidade", "indicadores": rentabilidade},
        ]
    }
