# Página de Análise — indicadores financeiros

Plano de implementação — branch `feat/analise` (partiu de `feat/graficos`).

## Objetivo

Adicionar uma **quinta aba**, "Análise", com 11 indicadores financeiros
(capítulos 10–11 do livro-base) em três famílias: Liquidez, Estrutura de Capital
e Rentabilidade.

O **backend calcula tudo**. O frontend apenas formata: não faz nenhuma conta,
nem divisão, nem multiplicação por 100 sobre valores brutos — cada indicador
chega pronto com nome, valor, fórmula em texto, nomes e valores do numerador e
do denominador, direção e formato.

Contrato de apresentação escolhido: **fórmula + valor + direção, sem veredito**.
Cada indicador é renderizado assim:

```
Liquidez Corrente          2,11
  Ativo Circulante / Passivo Circulante
  71.750,00 / 34.000,00
  ↑ quanto maior, melhor
```

## Restrições globais (valem para todas as tarefas)

- **Não altere o comportamento dos relatórios existentes nem dos gráficos.**
  `calcular_balancete`, `montar_bp`, `montar_dre`, `GraficoBalanco.jsx`,
  `GraficoDRE.jsx` e os `backend/tests/test_relatorios_*.py` já existentes
  permanecem exatamente como estão. Só se **lê** e **importa** deles. As
  exceções autorizadas são: acrescentar linhas novas ao fim de `schemas.py`,
  `api.js` e `index.css`; a nova aba em `App.jsx`; e o **comentário de
  cabeçalho** de `frontend/src/components/graficos-comuns.js` (Tarefa 3,
  passo 1) — comentário, zero risco de comportamento. O arquivo não é
  renomeado e nenhuma função dele é alterada.
- **Zero dependências novas**, backend ou frontend. `requirements.txt` e
  `package.json` não mudam.
- **Backend tem testes pytest de verdade** — é lógica de cálculo, é onde teste
  paga. Siga o estilo dos testes existentes (fixtures `db_session` e `client` de
  `backend/tests/conftest.py`, `Lancamento(...)` com `Decimal`, asserts diretos).
  A suíte hoje tem **20 testes passando**; ao fim deste plano deve ter **27**,
  com os 20 antigos intactos.
- **Sem testes automatizados de frontend.** Decisão de escopo deliberada e
  documentada do projeto. Não adicione Vitest/Jest/Testing Library. O **portão
  automatizado da tarefa de frontend é `npm run build` passando a partir de
  `frontend/`**. A verificação no navegador é feita depois, pelo coordenador —
  não pelo implementador da tarefa.
- **Idioma:** todas as strings visíveis ao usuário em português (pt-BR).
- **Estilo existente:** componentes de função, hooks, sem framework de CSS,
  `className` em strings simples, `style` inline só onde o código existente já
  usa.
- O app é **somente tema claro** (`frontend/src/index.css` não tem nenhuma regra
  `prefers-color-scheme`, de propósito). Não adicione nenhuma.
- Esta página é uma **tabela formatada, não um gráfico**. Não carregue a skill
  de dataviz, não introduza SVG, não escolha paleta.

## Regras de domínio que o plano inteiro respeita

1. **Divisão por zero aqui é rotina, não exceção.** Banco vazio dá PC = 0,
   PL = 0 e Receita = 0; uma empresa sem passivo circulante é legítima. Nesse
   caso o indicador devolve `valor = null` e um `motivo` curto
   (`"Passivo Circulante é zero."`), e a página mostra `—` com o motivo. Nunca
   `Infinity`, nunca `NaN`, nunca exceção.
2. **Denominador negativo faz o indicador mentir em silêncio, e a regra é
   geral — não uma lista de indicadores.** Com Patrimônio Líquido negativo,
   ROE = prejuízo ÷ PL negativo = número **positivo**: lê-se como retorno
   saudável de uma empresa insolvente. Com Receita negativa, Margem Líquida =
   −1.000 ÷ −500 = **+200%** para uma empresa de receita negativa. Mesma
   mentira, outro denominador — e não é hipótese: a fixture de casos extremos já
   produz um **CMV negativo**, prova de que estorno passando de zero acontece
   aqui. Por isso: **qualquer** indicador com denominador negativo devolve
   `valor = null`, `nao_significativo = true` e um motivo que explica. Uma
   checagem só, sobre o denominador — nada de flag por indicador, nada de
   enumeração para manter em sincronia quando um indicador novo entrar. É o
   mesmo princípio dos parágrafos `aviso` dos gráficos de BP e DRE já no
   repositório — recusar-se a afirmar algo falso e explicar em vez disso. Mesmo
   tom.
   Zero e negativo são casos **separados, com mensagens separadas**: zero dá
   `valor = null` + motivo e `nao_significativo = false`; negativo dá
   `valor = null` + motivo e `nao_significativo = true`.
3. **Giro do Ativo, ROA e ROE classicamente usam médias de dois períodos —
   ativo médio para Giro e ROA, PL médio (ou inicial) para ROE.** Este app tem
   um único período contínuo e usa os saldos finais. Além disso, o PL usado no
   ROE já inclui o resultado do período (regra do item acima), então o
   numerador do ROE está contido no seu próprio denominador — a fórmula
   clássica usa PL inicial ou médio justamente para evitar essa sobreposição.
   Nada disso é escondido: cada um dos três indicadores rotula sua própria
   ressalva no campo `observacao`.

## Explicitamente rejeitado — não adicione

Semáforo, classificação, veredito "bom/ruim", faixas de referência,
benchmarks setoriais, cores por faixa de valor. O raciocínio do usuário:
"liquidez corrente > 1,5 é bom" é falso para muitos setores, e ensinar a
simplificação como se fosse regra é pior do que não ensinar nada. Se algum passo
parecer pedir isso, ele não pede.

## Os 11 indicadores

| Família | Chave | Nome | Fórmula |
|---|---|---|---|
| Liquidez | `liquidez_corrente` | Liquidez Corrente | AC / PC |
| Liquidez | `liquidez_seca` | Liquidez Seca | (AC − Estoques) / PC |
| Liquidez | `liquidez_imediata` | Liquidez Imediata | (Caixa + Bancos) / PC |
| Estrutura de Capital | `participacao_capital_terceiros` | Participação de Capital de Terceiros | (PC + PNC) / PL |
| Estrutura de Capital | `composicao_endividamento` | Composição do Endividamento | PC / (PC + PNC) |
| Estrutura de Capital | `imobilizacao_pl` | Imobilização do PL | ANC / PL |
| Rentabilidade | `margem_bruta` | Margem Bruta | (Receita − CMV) / Receita |
| Rentabilidade | `margem_liquida` | Margem Líquida | Resultado / Receita |
| Rentabilidade | `roa` | ROA — Retorno sobre o Ativo | Resultado / Ativo Total |
| Rentabilidade | `roe` | ROE — Retorno sobre o PL | Resultado / PL |
| Rentabilidade | `giro_ativo` | Giro do Ativo | Receita / Ativo Total |

Códigos de conta fixos (de `backend/app/seed.py`): Caixa `1.1.01`, Bancos
`1.1.02`, Estoques `1.1.04`, CMV `4.1.01`. AC, ANC, PC, PNC e PL são subtotais
de grupo do balancete; **PL inclui o resultado do período**, igual ao que
`montar_bp` faz. Receita e Resultado vêm de `montar_dre`
(`total_receitas` e `resultado_periodo`).

**"Receita" nesta tabela é sempre a receita bruta** (`total_receitas` de
`montar_dre`), não a receita líquida de vendas que os livros-texto usam nas
margens. Esta aplicação não tem uma seção de deduções na DRE (Impostos sobre
Vendas é uma despesa, não uma dedução de receita), então não existe uma
receita líquida separada para usar. `total_receitas` também soma Receita de
Serviços, que não tem CMV associado — o que afeta especificamente Margem
Bruta.

---

## Tarefa 1 — `montar_analise` no backend

### Arquivos

- **Modificar:** `backend/app/relatorios.py`
- **Criar (teste):** `backend/tests/test_relatorios_analise.py`

### Interfaces

**Consome** (já existe em `backend/app/relatorios.py`, não altere):

- `calcular_balancete(db: Session) -> list[dict]` — cada dict tem
  `codigo`, `nome`, `grupo`, `tipo`, `total_debito`, `total_credito`, `saldo`.
- `montar_dre(db: Session) -> dict` — chaves `receitas`, `despesas`,
  `total_receitas`, `total_despesas`, `resultado_periodo`.
- De `app.models`: `Grupo` (valores `"Ativo Circulante"`,
  `"Ativo Não Circulante"`, `"Passivo Circulante"`,
  `"Passivo Não Circulante"`, `"Patrimônio Líquido"`) e `TipoConta`
  (`"patrimonial"`, `"resultado"`).

**Produz** (consumido pelas Tarefas 2 e 3):

```python
montar_analise(db: Session) -> dict
```

Formato de retorno:

```python
{
  "familias": [
    {
      "nome": "Liquidez",
      "indicadores": [ <indicador>, ... ],
    },
    { "nome": "Estrutura de Capital", "indicadores": [...] },
    { "nome": "Rentabilidade", "indicadores": [...] },
  ]
}
```

Cada `<indicador>` é um dict com exatamente estas chaves:

| Chave | Tipo | Significado |
|---|---|---|
| `chave` | `str` | identificador estável (ex.: `"liquidez_corrente"`) |
| `nome` | `str` | rótulo em pt-BR |
| `valor` | `float \| None` | `None` quando indisponível |
| `formula` | `str` | fórmula em texto, ex.: `"Ativo Circulante / Passivo Circulante"` |
| `numerador_nome` | `str` | ex.: `"Ativo Circulante − Estoques"` |
| `numerador_valor` | `float` | sempre preenchido, mesmo com `valor = None` |
| `denominador_nome` | `str` | ex.: `"Passivo Circulante"` |
| `denominador_valor` | `float` | sempre preenchido |
| `direcao` | `str` | `"maior_melhor"` ou `"menor_melhor"` |
| `formato` | `str` | `"indice"`, `"percentual"` ou `"vezes"` |
| `motivo` | `str \| None` | por que `valor` é `None` |
| `nao_significativo` | `bool` | `True` só no caso de denominador negativo marcado |
| `observacao` | `str \| None` | ressalva metodológica (só `giro_ativo` usa) |

Constantes exportadas do mesmo módulo (usadas nos testes e legíveis pela
Tarefa 3): `DIRECAO_MAIOR`, `DIRECAO_MENOR`, `FORMATO_INDICE`,
`FORMATO_PERCENTUAL`, `FORMATO_VEZES`.

### Passos

1. **Acrescente ao FIM de `backend/app/relatorios.py`** (depois de
   `montar_dre`) exatamente este bloco. Não mexa em nada acima dele.

```python
CODIGO_CAIXA = "1.1.01"
CODIGO_BANCOS = "1.1.02"
CODIGO_ESTOQUES = "1.1.04"
CODIGO_CMV = "4.1.01"

DIRECAO_MAIOR = "maior_melhor"
DIRECAO_MENOR = "menor_melhor"

FORMATO_INDICE = "indice"
FORMATO_PERCENTUAL = "percentual"
FORMATO_VEZES = "vezes"


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
```

2. **Crie `backend/tests/test_relatorios_analise.py`** com exatamente este
   conteúdo:

```python
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
```

3. **Rode o teste novo e veja falhar pelo motivo certo** — se você seguiu a
   ordem, o passo 1 já foi aplicado e ele passa; se quiser ver o vermelho
   primeiro, rode antes de aplicar o passo 1:

```
cd backend && pytest tests/test_relatorios_analise.py -v
```

   Antes do passo 1: `ImportError: cannot import name 'montar_analise' from
   'app.relatorios'`. Depois do passo 1: **6 passed**.

4. **Rode a suíte inteira:**

```
cd backend && pytest -v
```

   Esperado: **26 passed** (20 antigos + 6 novos). Nenhum dos 20 antigos pode
   falhar; se falhar, você mexeu em algo que não devia.

5. **Commit:**

```
git add backend/app/relatorios.py backend/tests/test_relatorios_analise.py
git commit -m "Adiciona montar_analise com os 11 indicadores financeiros"
```

---

## Tarefa 2 — Schemas e endpoint `GET /relatorios/analise`

### Arquivos

- **Modificar:** `backend/app/schemas.py`
- **Modificar:** `backend/app/routers/relatorios.py`
- **Modificar (teste):** `backend/tests/test_relatorios_analise.py`

### Interfaces

**Consome** (produzido pela Tarefa 1, já no repositório):

- `from app.relatorios import montar_analise` — `montar_analise(db: Session) -> dict`
  com `{"familias": [{"nome": str, "indicadores": [ ... ]}]}`. Cada indicador
  tem as chaves `chave`, `nome`, `valor` (`float | None`), `formula`,
  `numerador_nome`, `numerador_valor`, `denominador_nome`,
  `denominador_valor`, `direcao`, `formato`, `motivo` (`str | None`),
  `nao_significativo` (`bool`), `observacao` (`str | None`).
- Padrão existente em `backend/app/routers/relatorios.py`: `router =
  APIRouter(prefix="/relatorios")`, handlers com
  `db: Session = Depends(get_db)` e `response_model=`.

**Produz** (consumido pela Tarefa 3):

- Rota `GET /relatorios/analise`, resposta JSON validada por `AnaliseReport`.
  Os nomes de campo do JSON são exatamente os da tabela acima; `valor`,
  `motivo` e `observacao` podem vir `null`.
- Schemas em `app.schemas`: `IndicadorOut`, `FamiliaIndicadores`,
  `AnaliseReport`.

### Passos

1. **Acrescente ao FIM de `backend/app/schemas.py`** (depois de
   `UploadResultado`), sem alterar nada acima:

```python
class IndicadorOut(BaseModel):
    chave: str
    nome: str
    valor: Optional[float]
    formula: str
    numerador_nome: str
    numerador_valor: float
    denominador_nome: str
    denominador_valor: float
    direcao: str
    formato: str
    motivo: Optional[str] = None
    nao_significativo: bool = False
    observacao: Optional[str] = None


class FamiliaIndicadores(BaseModel):
    nome: str
    indicadores: list[IndicadorOut]


class AnaliseReport(BaseModel):
    familias: list[FamiliaIndicadores]
```

   `Optional` e `BaseModel` já estão importados no topo do arquivo; não
   acrescente imports.

2. **Em `backend/app/routers/relatorios.py`**, troque as duas linhas de import
   por estas (só acrescentam nomes):

```python
from app.relatorios import calcular_balancete, montar_bp, montar_dre, montar_analise
from app.schemas import BalanceteRow, BPReport, DREReport, AnaliseReport
```

3. **Acrescente ao FIM do mesmo arquivo**, depois de `obter_dre`:

```python
@router.get("/analise", response_model=AnaliseReport)
def obter_analise(db: Session = Depends(get_db)):
    return montar_analise(db)
```

4. **Acrescente ao FIM de `backend/tests/test_relatorios_analise.py`** este
   teste de endpoint (mantenha tudo que já está no arquivo):

```python
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
```

5. **Rode a suíte:**

```
cd backend && pytest -v
```

   Esperado: **27 passed** (20 antigos + 7 novos). Se `AnaliseReport` recusar
   algum campo, o teste falha com `ResponseValidationError` — é sinal de
   divergência entre o dict da Tarefa 1 e o schema; alinhe pelo dict, ele é a
   fonte.

6. **Commit:**

```
git add backend/app/schemas.py backend/app/routers/relatorios.py backend/tests/test_relatorios_analise.py
git commit -m "Expõe GET /relatorios/analise"
```

---

## Tarefa 3 — Página "Análise" no frontend

### Arquivos

- **Modificar:** `frontend/src/components/graficos-comuns.js` (só o comentário
  de cabeçalho)
- **Modificar:** `frontend/src/api.js`
- **Criar:** `frontend/src/pages/Analise.jsx`
- **Modificar:** `frontend/src/App.jsx`
- **Modificar:** `frontend/src/index.css`

### Interfaces

**Consome:**

- `GET http://localhost:8000/relatorios/analise` (Tarefa 2). Corpo:

```json
{
  "familias": [
    {
      "nome": "Liquidez",
      "indicadores": [
        {
          "chave": "liquidez_corrente",
          "nome": "Liquidez Corrente",
          "valor": 2.11029411764,
          "formula": "Ativo Circulante / Passivo Circulante",
          "numerador_nome": "Ativo Circulante",
          "numerador_valor": 71750.0,
          "denominador_nome": "Passivo Circulante",
          "denominador_valor": 34000.0,
          "direcao": "maior_melhor",
          "formato": "indice",
          "motivo": null,
          "nao_significativo": false,
          "observacao": null
        }
      ]
    }
  ]
}
```

  `direcao` ∈ `{"maior_melhor", "menor_melhor"}`;
  `formato` ∈ `{"indice", "percentual", "vezes"}`;
  `valor`, `motivo` e `observacao` podem ser `null`.
- `handleResponse` já existe em `frontend/src/api.js` (função interna, não
  exportada) — as funções `getX` existentes usam
  `fetch(...).then(handleResponse)`.
- `fmt` de `frontend/src/components/graficos-comuns.js`:
  `export function fmt(valor)` — `Intl.NumberFormat("pt-BR")` com 2 casas fixas
  (`71750` → `"71.750,00"`). **É o formatador certo para reusar aqui; não
  defina uma terceira cópia.** A única alteração permitida naquele arquivo é o
  comentário de cabeçalho (passo 1) — nenhuma função, nenhuma constante,
  nenhum rename.
- Estrutura de `App.jsx`: objeto `ABAS` mapeando chave → `{ rotulo, componente }`.

**Produz:**

- `export function getAnalise()` em `frontend/src/api.js` — devolve
  `Promise<{familias: [...]}>`.
- `frontend/src/pages/Analise.jsx` — `export default function Analise()`, sem
  props.
- Nova entrada `analise` em `ABAS`, rótulo `"Análise"`, última da lista.
- Classes CSS novas: `.analise-familia`, `.analise-tabela`, `.analise-nome`,
  `.analise-formula`, `.analise-substituicao`, `.analise-direcao`,
  `.analise-observacao`, `.analise-valor`, `.analise-motivo`,
  `.analise-nao-significativo`.

### Passos

1. **Atualize o comentário de cabeçalho de
   `frontend/src/components/graficos-comuns.js`.** A partir desta tarefa o
   arquivo passa a ser importado por uma página que não é gráfico, e o
   comentário atual passaria a descrever errado o próprio arquivo. Troque as
   quatro primeiras linhas:

```javascript
// Vocabulário compartilhado pelos gráficos de BP e DRE: formatação,
// cores de chrome/tinta e geometria de barra que são idênticas nos dois
// componentes. Não abstrai a estrutura dos gráficos em si — cada um
// mantém seu próprio layout, eixos e legenda.
```

   por estas quatro:

```javascript
// Vocabulário compartilhado de apresentação: formatação de número, cores de
// chrome/tinta e geometria de barra. Os gráficos de BP e DRE usam tudo; a
// página de Análise usa só o fmt. Não abstrai a estrutura dos gráficos em si —
// cada um mantém seu próprio layout, eixos e legenda.
```

   **Nada mais no arquivo muda** — nem `fmt`, nem as constantes de cor, nem
   `caminhoBarra`, e o arquivo não é renomeado.

2. **Acrescente ao FIM de `frontend/src/api.js`:**

```javascript
export function getAnalise() {
  return fetch(`${API_BASE}/relatorios/analise`).then(handleResponse);
}
```

3. **Crie `frontend/src/pages/Analise.jsx`** com exatamente este conteúdo:

```jsx
import { useEffect, useState } from "react";
import { getAnalise } from "../api";
import { fmt } from "../components/graficos-comuns";

const DIRECAO_ROTULO = {
  maior_melhor: "↑ quanto maior, melhor",
  menor_melhor: "↓ quanto menor, melhor",
};

// O backend já entregou o número pronto; aqui só se escolhe a máscara.
function formatarValor(valor, formato) {
  if (formato === "percentual") return `${fmt(valor * 100)}%`;
  if (formato === "vezes") return `${fmt(valor)} vezes`;
  return fmt(valor);
}

export default function Analise() {
  const [analise, setAnalise] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getAnalise()
      .then(setAnalise)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!analise) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Análise por Indicadores</h2>
      <p className="analise-intro">
        Cada indicador aparece com a fórmula, os valores substituídos e a direção
        de leitura. Não há classificação nem faixa de referência: o que é um bom
        índice depende do setor e do momento da empresa.
      </p>

      {analise.familias.map((familia) => (
        <div className="analise-familia" key={familia.nome}>
          <h3>{familia.nome}</h3>
          <table className="analise-tabela">
            <tbody>
              {familia.indicadores.map((indicador) => (
                <tr key={indicador.chave}>
                  <td>
                    <div className="analise-nome">{indicador.nome}</div>
                    <div className="analise-formula">{indicador.formula}</div>
                    <div className="analise-substituicao">
                      {fmt(indicador.numerador_valor)} / {fmt(indicador.denominador_valor)}
                    </div>
                    <div className="analise-direcao">
                      {DIRECAO_ROTULO[indicador.direcao]}
                    </div>
                    {indicador.observacao && (
                      <div className="analise-observacao">{indicador.observacao}</div>
                    )}
                  </td>
                  <td className="analise-valor">
                    {indicador.valor === null
                      ? "—"
                      : formatarValor(indicador.valor, indicador.formato)}
                    {indicador.motivo && (
                      <div
                        className={
                          indicador.nao_significativo
                            ? "analise-motivo analise-nao-significativo"
                            : "analise-motivo"
                        }
                      >
                        {indicador.motivo}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}
```

4. **Em `frontend/src/App.jsx`**, acrescente o import e a quinta aba. O arquivo
   inteiro fica assim nas duas primeiras seções (o resto não muda):

```jsx
import { useState } from "react";
import Lancamentos from "./pages/Lancamentos";
import Balancete from "./pages/Balancete";
import BalancoPatrimonial from "./pages/BalancoPatrimonial";
import DRE from "./pages/DRE";
import Analise from "./pages/Analise";

const ABAS = {
  lancamentos: { rotulo: "Lançamentos", componente: Lancamentos },
  balancete: { rotulo: "Balancete", componente: Balancete },
  bp: { rotulo: "Balanço Patrimonial", componente: BalancoPatrimonial },
  dre: { rotulo: "DRE", componente: DRE },
  analise: { rotulo: "Análise", componente: Analise },
};
```

5. **Acrescente ao FIM de `frontend/src/index.css`** (nenhuma regra
   `prefers-color-scheme`, nenhuma variável de tema):

```css
.analise-intro {
  font-size: 13px;
  color: #52514e;
  max-width: 60ch;
}

.analise-familia {
  margin-top: 24px;
}

.analise-familia h3 {
  margin: 0;
  font-size: 15px;
}

.analise-tabela td {
  vertical-align: top;
}

.analise-nome {
  font-weight: bold;
}

.analise-formula {
  font-size: 12px;
  color: #52514e;
  margin-top: 2px;
}

.analise-substituicao {
  font-family: ui-monospace, "Cascadia Mono", Menlo, Consolas, monospace;
  font-size: 12px;
  color: #52514e;
  margin-top: 2px;
}

.analise-direcao {
  font-size: 12px;
  color: #898781;
  margin-top: 2px;
}

.analise-observacao {
  font-size: 12px;
  color: #898781;
  margin-top: 4px;
  max-width: 52ch;
}

.analise-valor {
  text-align: right;
  white-space: nowrap;
  font-size: 18px;
  width: 40%;
}

.analise-motivo {
  font-size: 12px;
  font-weight: normal;
  color: #52514e;
  text-align: right;
  white-space: normal;
  margin-top: 4px;
}

.analise-nao-significativo {
  color: #92400e;
}
```

6. **Rode o portão de build:**

```
cd frontend && npm run build
```

   Esperado: build concluído sem erro (`vite build` terminando com a listagem de
   assets em `dist/`). Erro de import ou de JSX quebra aqui.

7. **Não escreva nem rode teste de frontend.** O projeto não tem framework de
   teste de frontend por decisão de escopo, e esta tarefa não introduz um. A
   verificação no navegador é do coordenador, com o checklist abaixo.

8. **Commit:**

```
git add frontend/src/components/graficos-comuns.js frontend/src/api.js frontend/src/pages/Analise.jsx frontend/src/App.jsx frontend/src/index.css
git commit -m "Adiciona a página Análise com os indicadores financeiros"
```

---

## Verificação manual (coordenador, depois das três tarefas)

Suba backend (`cd backend && uvicorn app.main:app --reload`) e frontend
(`cd frontend && npm run dev`).

### Base recém-criada, sem lançamentos

- [ ] A aba **Análise** existe, é a quinta, rotulada `Análise`.
- [ ] Os 11 indicadores aparecem, agrupados em Liquidez (3), Estrutura de
      Capital (3) e Rentabilidade (5).
- [ ] **Todos** mostram `—` no lugar do valor, com o motivo ao lado:
      `Passivo Circulante é zero.` (liquidez), `Patrimônio Líquido é zero.`
      (participação, imobilização, ROE), `Passivo Circulante + Passivo Não
      Circulante é zero.` (composição), `Receita é zero.` (margens),
      `Ativo Total é zero.` (ROA e giro).
- [ ] Nenhum `Infinity`, `NaN` ou `—%` na tela, e nenhum erro no console.
- [ ] As linhas de substituição mostram `0,00 / 0,00`.

### Importando `lancamentos_exemplo.csv` (18 lançamentos)

Base: AC 71.750,00 · ANC 8.000,00 · Ativo Total 79.750,00 · PC 34.000,00 ·
PNC 0,00 · PL 45.750,00 (Capital 50.000,00 + resultado −4.250,00) ·
Estoques 9.000,00 · Caixa 4.500,00 · Bancos 52.250,00 · Receita 20.500,00 ·
CMV 10.000,00 · Resultado −4.250,00.

| Indicador | Substituição exibida | Valor exibido |
|---|---|---|
| Liquidez Corrente | `71.750,00 / 34.000,00` | `2,11` |
| Liquidez Seca | `62.750,00 / 34.000,00` | `1,85` |
| Liquidez Imediata | `56.750,00 / 34.000,00` | `1,67` |
| Participação de Capital de Terceiros | `34.000,00 / 45.750,00` | `74,32%` |
| Composição do Endividamento | `34.000,00 / 34.000,00` | `100,00%` |
| Imobilização do Patrimônio Líquido | `8.000,00 / 45.750,00` | `17,49%` |
| Margem Bruta | `10.500,00 / 20.500,00` | `51,22%` |
| Margem Líquida | `-4.250,00 / 20.500,00` | `-20,73%` |
| ROA | `-4.250,00 / 79.750,00` | `-5,33%` |
| ROE | `-4.250,00 / 45.750,00` | `-9,29%` |
| Giro do Ativo | `20.500,00 / 79.750,00` | `0,26 vezes` |

- [ ] Todos os 11 valores batem com a tabela acima.
- [ ] Os três de Estrutura de Capital mostram `↓ quanto menor, melhor`; os
      outros oito mostram `↑ quanto maior, melhor`.
- [ ] O Giro do Ativo traz a ressalva sobre usar o ativo do fim do período em
      vez da média de dois períodos.
- [ ] Nenhum semáforo, cor por faixa, selo "bom/ruim" ou faixa de referência em
      lugar nenhum da página.
- [ ] As abas Balancete, Balanço Patrimonial e DRE continuam idênticas, com os
      gráficos funcionando.

### Base nova, importando `lancamentos_casos_extremos.csv` (4 lançamentos)

Base: AC 3.500,00 · ANC 0,00 · Ativo Total 3.500,00 · PC 8.000,00 · PNC 0,00 ·
PL **−4.500,00** (Capital 1.000,00 + resultado −5.500,00) · Estoques 0,00 ·
Caixa 500,00 · Bancos 1.000,00 · Receita 2.000,00 · CMV **−500,00**.

| Indicador | Substituição exibida | Valor exibido |
|---|---|---|
| Liquidez Corrente | `3.500,00 / 8.000,00` | `0,44` |
| Liquidez Seca | `3.500,00 / 8.000,00` | `0,44` |
| Liquidez Imediata | `1.500,00 / 8.000,00` | `0,19` |
| Participação de Capital de Terceiros | `8.000,00 / -4.500,00` | `—` + aviso |
| Composição do Endividamento | `8.000,00 / 8.000,00` | `100,00%` |
| Imobilização do Patrimônio Líquido | `0,00 / -4.500,00` | `—` + aviso |
| Margem Bruta | `2.500,00 / 2.000,00` | `125,00%` |
| Margem Líquida | `-5.500,00 / 2.000,00` | `-275,00%` |
| ROA | `-5.500,00 / 3.500,00` | `-157,14%` |
| ROE | `-5.500,00 / -4.500,00` | `—` + aviso |
| Giro do Ativo | `2.000,00 / 3.500,00` | `0,57 vezes` |

- [ ] Os três indicadores com PL no denominador mostram `—` e, em âmbar
      (`#92400e`, a mesma cor dos avisos dos gráficos), o texto explicando que o
      PL é negativo, que o quociente mudaria de sinal e que o indicador não é
      significativo neste caso.
- [ ] Essa fixture só exercita o ramo do PL: nela Receita (2.000,00) e Ativo
      Total (3.500,00) são positivos, então margens, ROA e giro **são**
      calculados. A regra em si é geral — quem cobre o caso de Receita negativa
      é o teste `test_analise_marca_nao_significativo_com_receita_negativa`.
- [ ] **Em nenhum lugar** aparece um ROE positivo. Se aparecer `122,22%` no ROE,
      o caminho de denominador negativo não está funcionando — é exatamente o
      número mentiroso que este plano existe para evitar.
- [ ] Margem Bruta acima de 100% (CMV negativo por estorno) é exibida como
      `125,00%`, sem tratamento especial no *valor* — o dado está certo, é a
      razão que é atípica. A *causa*, porém, agora é surfaced: a observação do
      indicador cita o CMV negativo (`-500,00`) e sugere verificar estornos em
      Lançamentos.

### Portões automatizados

- [ ] `cd backend && pytest -v` → **27 passed** (20 antigos intactos + 7 novos).
- [ ] `cd frontend && npm run build` → sucesso.
- [ ] `git diff feat/graficos -- frontend/src/components/` mostra **apenas** as
      quatro linhas de comentário do cabeçalho de `graficos-comuns.js` — nenhuma
      linha de código, nenhum arquivo de gráfico tocado.
- [ ] `git diff --stat feat/graficos` não lista `backend/app/relatorios.py`
      além do bloco acrescentado ao fim.
