# Comparação entre períodos — plano de implementação

Fonte: `docs/superpowers/specs/2026-09-21-comparacao-periodos-design.md` (aprovado).

Branch: `feat/comparacao-periodos`, criada a partir do HEAD atual
(`fix/balancete-subtotal-datas-ptbr`). Antes da Tarefa 1:

```
git checkout -b feat/comparacao-periodos
```

## O que este trabalho entrega

Uma **sexta aba**, "Comparação", que mostra Balanço Patrimonial e DRE de dois
períodos lado a lado, com coluna de variação percentual. Para isso, o backend
ganha filtros de data **opcionais** em `calcular_balancete`, `montar_bp` e
`montar_dre`, e os endpoints `/relatorios/bp` e `/relatorios/dre` ganham query
params opcionais.

A distinção que governa tudo: **BP é foto** (acumulado desde o início até uma
data de corte) e **DRE é fluxo** (o que ocorreu dentro de um intervalo). Por
isso a tela tem **4 campos de data, não 6**: a data de *fim* de cada período é
ao mesmo tempo o `data_corte` do BP e o `data_fim` da DRE daquele período; a
data de *início* alimenta só a DRE.

## Restrições globais (valem para todas as tarefas)

- **Zero dependências novas.** `frontend/package.json` e
  `backend/requirements.txt` não podem aparecer no diff.
- **O caso sem argumentos tem de continuar idêntico ao de hoje.**
  `calcular_balancete(db)`, `montar_bp(db)` e `montar_dre(db)` sem os novos
  parâmetros somam a base inteira, sem nenhum corte — nem sequer por "hoje".
  Cada tarefa de backend traz o teste de regressão literal que prova isso.
- **`montar_analise` não muda.** Não é editada, não ganha teste novo, não é
  renomeada. Ela continua chamando `calcular_balancete(db)` e `montar_dre(db)`
  sem argumentos, e isso passa a funcionar sozinho porque os parâmetros novos
  são opcionais. Se alguma tarefa parecer exigir tocar em `montar_analise`,
  **pare e reporte** — é defeito de plano, não é para contornar.
- **As quatro páginas existentes não mudam de comportamento.**
  `Lancamentos.jsx`, `Balancete.jsx`, `BalancoPatrimonial.jsx`, `DRE.jsx` e
  `Analise.jsx` continuam sem seletor de data. `BalancoPatrimonial.jsx` e
  `DRE.jsx` **não são editados**: as chamadas `getBP()` e `getDRE()` sem
  argumentos continuam válidas depois da Tarefa 3.
- **Sem framework de teste de frontend.** Decisão de escopo deliberada do
  projeto. Não adicione Vitest/Jest/Testing Library. O portão automatizado das
  tarefas de frontend é `npm run build` passando a partir de `frontend/`. A
  verificação visual é feita no navegador pelo coordenador, depois.
- **Backend tem pytest de verdade.** Fixtures `db_session` e `client` de
  `backend/tests/conftest.py`, `Lancamento(...)` com `Decimal`, asserts diretos
  — o estilo dos testes já existentes. A suíte hoje tem **29 testes passando**;
  ao fim da Tarefa 1 deve ter **36**, e ao fim da Tarefa 2, **39**, com os 29
  antigos intactos.
- **Idioma:** toda string visível ao usuário em português (pt-BR).
- **Tema claro apenas.** Nenhuma regra `prefers-color-scheme` no CSS.
- **Não reutilize `.bp-coluna`/`.bp-colunas`.** O fio vertical daquela classe
  significa especificamente débito/crédito (a conta T). Na página nova, duas
  colunas significam **tempo** — outro eixo. Classes novas, prefixo
  `.comparacao-`.
- **Variação % é aritmética de exibição, no frontend**, na mesma categoria de
  `fmt`/`classeValor` — não é lógica contábil nova. Passa por `arredondar`
  antes e depois da divisão (Tarefa 4 explica por quê, com números).

## Tarefa 1 — filtro de data em `calcular_balancete`, `montar_bp` e `montar_dre`

### Arquivos

- `backend/app/relatorios.py` — **modificar**
- `backend/tests/test_relatorios_balancete.py` — **modificar** (3 testes novos)
- `backend/tests/test_relatorios_bp.py` — **modificar** (2 testes novos)
- `backend/tests/test_relatorios_dre.py` — **modificar** (2 testes novos)

### Interfaces

Produz (consumidas pelas Tarefas 2 e 4, via HTTP):

```python
def _lancamentos_dataframe(db: Session, data_inicio: date | None = None, data_fim: date | None = None) -> pd.DataFrame
def calcular_balancete(db: Session, data_inicio: date | None = None, data_fim: date | None = None) -> list[dict]
def montar_bp(db: Session, data_corte: date | None = None) -> dict
def montar_dre(db: Session, data_inicio: date | None = None, data_fim: date | None = None) -> dict
```

Inalteradas, e nenhuma delas é editada: `_contas_dataframe`,
`montar_balancete`, `_agrupar_secoes`, `_formatar_pt_br`, `_indicador`,
`montar_analise`.

A forma dos dicionários de retorno **não muda** — `montar_bp` continua
devolvendo `ativo`/`passivo_pl`/`total_ativo`/`total_passivo_pl`/`balanceado`,
e `montar_dre` continua devolvendo
`receitas`/`despesas`/`total_receitas`/`total_despesas`/`resultado_periodo`.
Por isso `backend/app/schemas.py` **não é tocado** nesta tarefa nem em nenhuma
outra deste plano.

### Passos

1. **Escreva os 3 testes novos de balancete** ao fim de
   `backend/tests/test_relatorios_balancete.py` (o arquivo já importa
   `Decimal`, `date`, `Lancamento`, `calcular_balancete` e `montar_balancete` —
   nenhum import novo é necessário):

```python
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
```

   Conferência das contas, na mão: 1000 + 200 + 40 = **1240**; 100 + 25 =
   **125**. Caixa é devedora (saldo = débito − crédito = 1240 − 0); Capital
   Social é credora (saldo = crédito − débito = 1240 − 0).

2. **Escreva os 2 testes novos de BP** ao fim de
   `backend/tests/test_relatorios_bp.py` (imports já presentes: `Decimal`,
   `date`, `Lancamento`, `montar_bp`):

```python
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
```

   Conferência do primeiro teste, na mão. Até 31/01 inclusive entram os dois
   primeiros lançamentos. Caixa: débito 5000, crédito 0 → 5000. Estoques:
   débito 2000 → 2000. Imobilizado: 0. Ativo Circulante = 5000 + 2000 = 7000;
   Ativo Não Circulante = 0; total do ativo = 7000. Fornecedores (credora):
   crédito 2000 → 2000. Passivo Não Circulante = 0. Capital Social = 5000.
   Nenhuma conta de resultado foi movimentada, então a linha sintética
   `RESULTADO` entra com 0.00 e o PL fica 5000. Total do passivo + PL = 2000 +
   0 + 5000 = **7000**. Fecha.

3. **Escreva os 2 testes novos de DRE** ao fim de
   `backend/tests/test_relatorios_dre.py` (imports já presentes: `Decimal`,
   `date`, `Lancamento`, `montar_dre`):

```python
def test_montar_dre_filtra_por_intervalo(db_session):
    db_session.add_all([
        # Receita antes do início: fora.
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("1000.00"), historico="Venda de janeiro"),
        # Dentro do intervalo.
        Lancamento(data=date(2026, 2, 10), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00"), historico="Venda de fevereiro"),
        Lancamento(data=date(2026, 2, 20), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00"), historico="Baixa de CMV"),
        # Despesa depois do fim: fora.
        Lancamento(data=date(2026, 3, 1), conta_debito="4.1.02", conta_credito="1.1.01", valor=Decimal("500.00"), historico="Aluguel de março"),
    ])
    db_session.commit()

    dre = montar_dre(db_session, data_inicio=date(2026, 2, 1), data_fim=date(2026, 2, 28))

    assert dre["total_receitas"] == 3000.00
    assert dre["total_despesas"] == 1200.00
    assert dre["resultado_periodo"] == 1800.00

    # As linhas não somem no recorte: a conta fora do intervalo aparece zerada.
    # É o que garante que os dois períodos da comparação casem linha a linha.
    assert len(dre["receitas"]) == 2
    assert len(dre["despesas"]) == 5
    administrativas = next(c for c in dre["despesas"] if c["codigo"] == "4.1.02")
    assert administrativas["valor"] == 0.0


def test_montar_dre_sem_parametros_soma_todos_os_periodos(db_session):
    # Regressão: sem intervalo, a DRE continua sendo o período contínuo único
    # de hoje — acumula tudo desde o primeiro lançamento.
    db_session.add_all([
        Lancamento(data=date(2026, 1, 31), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("1000.00")),
        Lancamento(data=date(2026, 2, 10), conta_debito="1.1.03", conta_credito="3.1.01", valor=Decimal("3000.00")),
        Lancamento(data=date(2026, 2, 20), conta_debito="4.1.01", conta_credito="1.1.04", valor=Decimal("1200.00")),
        Lancamento(data=date(2026, 3, 1), conta_debito="4.1.02", conta_credito="1.1.01", valor=Decimal("500.00")),
    ])
    db_session.commit()

    dre = montar_dre(db_session)

    assert dre["total_receitas"] == 4000.00
    assert dre["total_despesas"] == 1700.00
    assert dre["resultado_periodo"] == 2300.00
```

   Conferência, na mão. Filtrado: receita 3000; despesa 1200; 3000 − 1200 =
   **1800**. Sem filtro: receitas 1000 + 3000 = **4000**; despesas 1200 + 500 =
   **1700**; 4000 − 1700 = **2300**. O seed tem 2 contas de receita (3.1.01,
   3.1.02) e 5 de despesa (4.1.01 a 4.1.05).

4. **Rode os testes e veja os 4 testes de filtro falharem:**

```
cd backend && python -m pytest -q
```

   Esperado: `4 failed, 32 passed`. Os 4 que falham são os que passam
   parâmetro novo — `test_calcular_balancete_filtra_por_intervalo`,
   `test_calcular_balancete_intervalo_inclui_as_datas_de_borda`,
   `test_montar_bp_com_data_corte_soma_ate_a_data_inclusive` e
   `test_montar_dre_filtra_por_intervalo` — todos com `TypeError`
   (`calcular_balancete() got an unexpected keyword argument 'data_inicio'`,
   `montar_bp() got an unexpected keyword argument 'data_corte'`,
   `montar_dre() got an unexpected keyword argument 'data_inicio'`). Os 3
   testes de regressão (`test_calcular_balancete_sem_parametros_soma_todos_os_periodos`,
   `test_montar_bp_sem_data_corte_inclui_lancamento_futuro`,
   `test_montar_dre_sem_parametros_soma_todos_os_periodos`) **passam já nesta
   rodada, e isso é esperado**: eles descrevem o comportamento de hoje, que o
   filtro não pode quebrar. Se algum dos 4 primeiros passar agora, pare — o
   teste não está exercitando o filtro.

5. **Implemente o filtro em `backend/app/relatorios.py`.** Acrescente o import
   de `date` no topo do arquivo, logo antes do import de `pandas`:

```python
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Lancamento, ContaContabil, Natureza, Grupo, TipoConta
```

   Substitua `_lancamentos_dataframe` (hoje nas linhas 7–13) por:

```python
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
```

6. **Repasse os parâmetros em `calcular_balancete`.** Troque a assinatura e a
   primeira linha do corpo (hoje linhas 30–31); o resto da função não muda:

```python
def calcular_balancete(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[dict]:
    lanc_df = _lancamentos_dataframe(db, data_inicio=data_inicio, data_fim=data_fim)
    contas_df = _contas_dataframe(db)
```

7. **Troque a assinatura e a primeira linha de `montar_bp`** (hoje linhas
   98–99). O resto da função — filtros por tipo, `_agrupar_secoes`, a linha
   sintética `RESULTADO`, `balanceado` — fica exatamente como está:

```python
def montar_bp(db: Session, data_corte: date | None = None) -> dict:
    # BP é foto: acumula desde o primeiro lançamento até `data_corte`, que por
    # isso entra como `data_fim` e não tem contraparte de início.
    balancete = calcular_balancete(db, data_fim=data_corte)
```

8. **Troque a assinatura e a primeira linha de `montar_dre`** (hoje linhas
   128–129). O resto da função fica como está:

```python
def montar_dre(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> dict:
    # DRE é fluxo: só o que ocorreu dentro do intervalo. Sem os parâmetros, o
    # comportamento de hoje continua — período contínuo único, desde o início.
    balancete = calcular_balancete(db, data_inicio=data_inicio, data_fim=data_fim)
```

9. **Não toque em `montar_analise`.** Confirme que ela continua com
   `balancete = calcular_balancete(db)` e `dre = montar_dre(db)`, sem
   argumentos novos. `git diff backend/app/relatorios.py` não pode mostrar
   nenhuma linha alterada abaixo de `def montar_analise`.

10. **Rode os testes de novo:**

```
cd backend && python -m pytest -q
```

   Esperado: `36 passed`.

11. **Confirme que nenhuma dependência entrou:**

```
git diff --stat backend/requirements.txt
```

   Esperado: saída vazia.

12. **Commit:**

```
git add backend/app/relatorios.py backend/tests/test_relatorios_balancete.py backend/tests/test_relatorios_bp.py backend/tests/test_relatorios_dre.py
git commit -m "Filtro de data opcional em calcular_balancete, montar_bp e montar_dre"
```

## Tarefa 2 — query params nos endpoints `/relatorios/bp` e `/relatorios/dre`

### Arquivos

- `backend/app/routers/relatorios.py` — **modificar**
- `backend/tests/test_relatorios_bp.py` — **modificar** (2 testes novos)
- `backend/tests/test_relatorios_dre.py` — **modificar** (1 teste novo)

### Interfaces

Consome da Tarefa 1:

```python
def montar_bp(db: Session, data_corte: date | None = None) -> dict
def montar_dre(db: Session, data_inicio: date | None = None, data_fim: date | None = None) -> dict
```

Produz (consumido pela Tarefa 3, via HTTP) — **nomes exatos dos query params**:

```
GET /relatorios/bp                                           -> BPReport
GET /relatorios/bp?data_corte=AAAA-MM-DD                     -> BPReport
GET /relatorios/dre                                          -> DREReport
GET /relatorios/dre?data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD -> DREReport
```

Os dois parâmetros da DRE são independentes: passar só um é válido. Data em
formato inválido devolve **422** (validação do FastAPI, nenhum tratamento
manual). `BPReport` e `DREReport` em `backend/app/schemas.py` **não mudam**.
Os endpoints `/relatorios/balancete` e `/relatorios/analise` **não mudam**.

### Passos

1. **Escreva os 2 testes novos de endpoint de BP** ao fim de
   `backend/tests/test_relatorios_bp.py`:

```python
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
```

   Conferência: 500 até 31/01; 500 + 300 = **800** sem corte.

2. **Escreva o teste novo de endpoint de DRE** ao fim de
   `backend/tests/test_relatorios_dre.py`:

```python
def test_endpoint_dre_com_intervalo(client):
    client.post("/lancamentos", json={"data": "2026-01-31", "conta_debito": "1.1.03", "conta_credito": "3.1.01", "valor": 1000.0})
    client.post("/lancamentos", json={"data": "2026-02-10", "conta_debito": "1.1.03", "conta_credito": "3.1.01", "valor": 3000.0})
    client.post("/lancamentos", json={"data": "2026-03-01", "conta_debito": "4.1.02", "conta_credito": "1.1.01", "valor": 500.0})

    resposta = client.get("/relatorios/dre?data_inicio=2026-02-01&data_fim=2026-02-28")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_receitas"] == 3000.0
    assert corpo["total_despesas"] == 0.0
    assert corpo["resultado_periodo"] == 3000.0

    # Sem os parâmetros, o mesmo endpoint continua acumulando tudo.
    resposta = client.get("/relatorios/dre")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_receitas"] == 4000.0
    assert corpo["total_despesas"] == 500.0
    assert corpo["resultado_periodo"] == 3500.0
```

   Conferência: no intervalo de fevereiro só entra a venda de 3000, nenhuma
   despesa → resultado **3000**. Sem filtro: receitas 1000 + 3000 = **4000**,
   despesas **500**, resultado 4000 − 500 = **3500**.

3. **Rode os testes e veja os 3 novos falharem:**

```
cd backend && python -m pytest -q
```

   Esperado: `3 failed, 36 passed`. As falhas vêm dos query params ainda
   ignorados — `total_ativo` volta 800.0 onde o teste espera 500.0, a DRE
   filtrada volta 4000.0 onde o teste espera 3000.0, e o teste de data
   inválida recebe 200 em vez de 422.

4. **Reescreva `backend/app/routers/relatorios.py` inteiro** (arquivo tem 28
   linhas hoje) com este conteúdo:

```python
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.relatorios import montar_balancete, montar_bp, montar_dre, montar_analise
from app.schemas import BalanceteReport, BPReport, DREReport, AnaliseReport

router = APIRouter(prefix="/relatorios")


@router.get("/balancete", response_model=BalanceteReport)
def obter_balancete(db: Session = Depends(get_db)):
    return montar_balancete(db)


# BP é foto: uma data de corte só, sem início — o saldo acumula desde o
# primeiro lançamento. Sem o parâmetro, soma a base inteira, como antes.
@router.get("/bp", response_model=BPReport)
def obter_bp(data_corte: date | None = None, db: Session = Depends(get_db)):
    return montar_bp(db, data_corte=data_corte)


# DRE é fluxo: um intervalo. Os dois parâmetros são independentes e opcionais;
# sem nenhum deles, o comportamento é o de hoje.
@router.get("/dre", response_model=DREReport)
def obter_dre(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
):
    return montar_dre(db, data_inicio=data_inicio, data_fim=data_fim)


@router.get("/analise", response_model=AnaliseReport)
def obter_analise(db: Session = Depends(get_db)):
    return montar_analise(db)
```

5. **Rode os testes:**

```
cd backend && python -m pytest -q
```

   Esperado: `39 passed`.

6. **Commit:**

```
git add backend/app/routers/relatorios.py backend/tests/test_relatorios_bp.py backend/tests/test_relatorios_dre.py
git commit -m "Query params opcionais de data em /relatorios/bp e /relatorios/dre"
```

## Tarefa 3 — `getBP`/`getDRE` aceitam datas opcionais

### Arquivos

- `frontend/src/api.js` — **modificar**

### Interfaces

Consome da Tarefa 2: os query params `data_corte` (BP) e
`data_inicio`/`data_fim` (DRE), em ISO `AAAA-MM-DD` — exatamente o formato que
um `<input type="date">` produz em `e.target.value`, sem conversão.

Produz (consumido pela Tarefa 4):

```js
getBP(dataCorte?: string) -> Promise<BPReport>
getDRE(dataInicio?: string, dataFim?: string) -> Promise<DREReport>
```

Argumento ausente, `undefined` ou string vazia **omite** o parâmetro da URL.
`getBP()` e `getDRE()` sem argumentos montam exatamente a URL de hoje — é o que
mantém `BalancoPatrimonial.jsx` e `DRE.jsx` funcionando sem edição. As outras
funções exportadas (`getContas`, `getLancamentos`, `criarLancamento`,
`uploadLancamentos`, `getBalancete`, `getAnalise`), `API_BASE` e
`handleResponse` **não mudam**.

### Passos

1. **Substitua as funções `getBP` e `getDRE`** em `frontend/src/api.js` (hoje
   linhas 44–50) por:

```js
// Monta "?a=1&b=2" a partir dos parâmetros preenchidos, ou "" se nenhum veio.
// Valor vazio é omitido, não enviado em branco: o backend trata parâmetro
// ausente como "sem filtro", e "" não é uma data válida — viraria 422.
function querystring(parametros) {
  const busca = new URLSearchParams();
  Object.entries(parametros).forEach(([chave, valor]) => {
    if (valor) busca.set(chave, valor);
  });
  const texto = busca.toString();
  return texto ? `?${texto}` : "";
}

// `dataCorte` em ISO (AAAA-MM-DD), o formato que <input type="date"> devolve.
// Sem argumento, a URL é a mesma de sempre e o BP soma a base inteira.
export function getBP(dataCorte) {
  return fetch(
    `${API_BASE}/relatorios/bp${querystring({ data_corte: dataCorte })}`
  ).then(handleResponse);
}

export function getDRE(dataInicio, dataFim) {
  return fetch(
    `${API_BASE}/relatorios/dre${querystring({ data_inicio: dataInicio, data_fim: dataFim })}`
  ).then(handleResponse);
}
```

2. **Confirme que nenhuma página existente foi editada:**

```
git status --short frontend/src
```

   Esperado: só `frontend/src/api.js` modificado.

3. **Rode o build:**

```
cd frontend && npm run build
```

   Esperado: build concluído sem erro (`✓ built in ...`).

4. **Commit:**

```
git add frontend/src/api.js
git commit -m "getBP e getDRE aceitam datas opcionais"
```

## Tarefa 4 — página "Comparação", CSS e a nova aba

### Arquivos

- `frontend/src/pages/Comparacao.jsx` — **criar**
- `frontend/src/index.css` — **modificar** (bloco novo + 1 seletor acrescentado
  a uma regra existente + 1 regra na media query)
- `frontend/src/App.jsx` — **modificar** (import + entrada em `ABAS`)

### Interfaces

Consome da Tarefa 3:

```js
import { getBP, getDRE } from "../api";
getBP(dataCorte)             // dataCorte: "AAAA-MM-DD"
getDRE(dataInicio, dataFim)  // ambos "AAAA-MM-DD"
```

Consome de `frontend/src/components/graficos-comuns.js`, sem alterá-lo:
`fmt(valor)`, `classeValor(valor)` (devolve `"razao-valor"` ou
`"razao-valor valor-negativo"`), `arredondar(valor)` (2 casas, normaliza o zero
negativo) e `formatarData(iso)` (rearranjo de string ISO → `DD/MM/AAAA`; **não**
usar em `<input type="date">`, que exige ISO).

Forma das respostas consumidas (não mudam neste plano):

```
BPReport:  { ativo: [{grupo, contas: [{codigo, nome, saldo}], subtotal}],
             passivo_pl: [... mesma forma ...],
             total_ativo, total_passivo_pl, balanceado }
DREReport: { receitas: [{codigo, nome, valor}], despesas: [...],
             total_receitas, total_despesas, resultado_periodo }
```

Produz: `export default function Comparacao()` em
`frontend/src/pages/Comparacao.jsx`, e a chave `comparacao` no dicionário
`ABAS` de `App.jsx`. Classes CSS novas, todas com prefixo `comparacao-`:
`.comparacao-intro`, `.comparacao-form`, `.comparacao-aviso`,
`.comparacao-legenda`, `.comparacao-conta`, `.comparacao-vazio`.

### Por que o pareamento linha a linha é seguro

`calcular_balancete` itera o plano de contas inteiro sempre, com filtro ou sem
— uma conta sem lançamento no recorte sai com saldo `0.0`, nunca some da lista
(provado pelos testes da Tarefa 1). Logo os dois BPs têm as mesmas seções na
mesma ordem, com as mesmas contas na mesma ordem, e as duas DREs têm as mesmas
receitas e despesas na mesma ordem. `montar_bp` acrescenta a linha sintética
`RESULTADO` ao Patrimônio Líquido nos dois casos. Por isso o pareamento por
índice é correto, e não é preciso casar por código de conta.

### Por que a variação % passa por `arredondar` três vezes

Fórmula: `(valor2 − valor1) / Math.abs(valor1)`, vezes 100.

- **Base zero.** `valor1 === 0` não tem divisão: devolve `null`, e a célula
  imprime `—`. Nunca `Infinity%`, nunca `NaN%`.
- **Base com resíduo.** O backend soma floats crus. Uma base de `1e-9` daria
  uma variação de dezenas de bilhões de por cento em vez de `—`. Por isso a
  base passa por `arredondar` **antes** do teste de zero: `arredondar(1e-9)`
  é `0`, e o caso vira `—`, que é a leitura certa.
- **Zero negativo.** `Math.round(-0.5)` é `-0` em JS. Sem normalizar, uma
  variação nula imprimiria `-0,00%` em vermelho. `arredondar` já devolve `0`
  para `-0`, e é por isso que o **resultado** também passa por ele antes de
  `fmt` e de `classeValor`.
- **Base negativa.** Dividir por `Math.abs(valor1)`, não por `valor1`, é o que
  evita a inversão de sinal que estraga indicadores de denominador negativo na
  página de Análise. Aqui os dois operandos são a **mesma grandeza em dois
  instantes**, então a divisão pelo módulo lê certo. Conferência na mão:
  resultado de −1000 para −500 (prejuízo menor, melhora) dá
  `(−500 − (−1000)) / 1000 × 100 = +50,00%`. De −500 para −1000 (piora) dá
  `(−1000 − (−500)) / 500 × 100 = −100,00%`. De 1000 para 1500 dá `+50,00%`;
  de 300 para 0 dá `−100,00%`; de 1000 para 1000,000001 dá `0,00%` (porque
  `arredondar(1000.000001)` é `1000`), não `+0,00%` nem `-0,00%`.

### Passos

1. **Crie `frontend/src/pages/Comparacao.jsx`** com exatamente este conteúdo:

```jsx
import { useState } from "react";
import { getBP, getDRE } from "../api";
import { fmt, classeValor, arredondar, formatarData } from "../components/graficos-comuns";

const PERIODO_VAZIO = { inicio: "", fim: "" };

// Variação percentual entre dois instantes da MESMA grandeza — aritmética de
// exibição, da mesma família de `fmt` e `classeValor`, não cálculo contábil.
//
// Devolve null quando a base é zero: a divisão não existe e a página mostra
// "—", nunca Infinity nem NaN. Os dois operandos passam por `arredondar` ANTES
// da divisão porque o backend soma floats crus: uma base de resíduo (1e-9)
// produziria bilhões de por cento em vez de "—". O resultado passa por
// `arredondar` de novo porque Math.round devolve -0 para quedas ínfimas, e
// "-0,00%" em vermelho é o bug de sinal que este projeto já corrigiu duas
// vezes. Divide por Math.abs(base), não por base: com base negativa é isso que
// preserva o sentido de melhora/piora (−1000 -> −500 dá +50%).
function variacaoPercentual(valor1, valor2) {
  const base = arredondar(valor1);
  if (base === 0) return null;
  return arredondar(((arredondar(valor2) - base) / Math.abs(base)) * 100);
}

function textoVariacao(percentual) {
  if (percentual === null) return "—";
  return `${percentual > 0 ? "+" : ""}${fmt(percentual)}%`;
}

function classeVariacao(percentual) {
  return percentual === null ? "razao-valor" : classeValor(percentual);
}

function TabelaComparacao({ linhas }) {
  return (
    <table>
      <thead>
        <tr>
          <th className="comparacao-conta">Conta</th>
          <th className="razao-valor">Período 1</th>
          <th className="razao-valor">Período 2</th>
          <th className="razao-valor">Variação</th>
        </tr>
      </thead>
      <tbody>
        {linhas.map((linha) => {
          const percentual = variacaoPercentual(linha.valor1, linha.valor2);
          return (
            <tr key={linha.chave} className={linha.className}>
              <td>{linha.rotulo}</td>
              <td className={classeValor(linha.valor1)}>{fmt(linha.valor1)}</td>
              <td className={classeValor(linha.valor2)}>{fmt(linha.valor2)}</td>
              <td className={classeVariacao(percentual)}>{textoVariacao(percentual)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// Pareia por índice, não por código: calcular_balancete percorre o plano de
// contas inteiro com filtro ou sem ele, então os dois períodos têm sempre as
// mesmas seções e as mesmas contas, na mesma ordem — conta sem movimento no
// recorte vem com saldo 0, não some.
function linhasDasSecoes(secoes1, secoes2) {
  const linhas = [];
  secoes1.forEach((secao1, i) => {
    const secao2 = secoes2[i];
    secao1.contas.forEach((conta1, j) => {
      linhas.push({
        chave: `${secao1.grupo}-${conta1.codigo}`,
        rotulo: conta1.nome,
        valor1: conta1.saldo,
        valor2: secao2.contas[j].saldo,
      });
    });
    linhas.push({
      chave: `${secao1.grupo}-subtotal`,
      rotulo: `Subtotal — ${secao1.grupo}`,
      valor1: secao1.subtotal,
      valor2: secao2.subtotal,
      className: "razao-subtotal",
    });
  });
  return linhas;
}

function linhasDasContas(contas1, contas2, prefixo) {
  return contas1.map((conta1, i) => ({
    chave: `${prefixo}-${conta1.codigo}`,
    rotulo: conta1.nome,
    valor1: conta1.valor,
    valor2: contas2[i].valor,
  }));
}

function linhaTotal(chave, rotulo, valor1, valor2) {
  return {
    chave,
    rotulo,
    valor1,
    valor2,
    className: "razao-subtotal razao-total-tabela",
  };
}

export default function Comparacao() {
  const [periodo1, setPeriodo1] = useState(PERIODO_VAZIO);
  const [periodo2, setPeriodo2] = useState(PERIODO_VAZIO);
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);

  // Datas ISO (AAAA-MM-DD) comparam certo como string: os campos são de
  // largura fixa e vão do mais significativo ao menos.
  const invertido1 = periodo1.inicio !== "" && periodo1.fim !== "" && periodo1.inicio > periodo1.fim;
  const invertido2 = periodo2.inicio !== "" && periodo2.fim !== "" && periodo2.inicio > periodo2.fim;

  async function aoComparar(evento) {
    evento.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      const [bp1, bp2, dre1, dre2] = await Promise.all([
        getBP(periodo1.fim),
        getBP(periodo2.fim),
        getDRE(periodo1.inicio, periodo1.fim),
        getDRE(periodo2.inicio, periodo2.fim),
      ]);
      // Guarda os períodos junto com os dados: as legendas têm de mostrar o
      // que foi consultado, não o que o usuário digitou depois.
      setDados({ bp1, bp2, dre1, dre2, p1: periodo1, p2: periodo2 });
    } catch (e) {
      setErro(e.message);
      setDados(null);
    }
    setCarregando(false);
  }

  return (
    <section>
      <h2>Comparação entre períodos</h2>
      <p className="comparacao-intro">
        O Balanço Patrimonial é uma foto: acumula tudo desde o primeiro
        lançamento até a data de fim do período. A DRE é fluxo: só o que ocorreu
        dentro do intervalo. Por isso a data de fim alimenta os dois relatórios
        e a data de início alimenta só a DRE.
      </p>

      <form className="comparacao-form" onSubmit={aoComparar}>
        <label className="campo">
          <span className="campo-rotulo">Período 1 — início</span>
          <input
            type="date"
            value={periodo1.inicio}
            onChange={(e) => setPeriodo1({ ...periodo1, inicio: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Período 1 — fim</span>
          <input
            type="date"
            value={periodo1.fim}
            onChange={(e) => setPeriodo1({ ...periodo1, fim: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Período 2 — início</span>
          <input
            type="date"
            value={periodo2.inicio}
            onChange={(e) => setPeriodo2({ ...periodo2, inicio: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Período 2 — fim</span>
          <input
            type="date"
            value={periodo2.fim}
            onChange={(e) => setPeriodo2({ ...periodo2, fim: e.target.value })}
            required
          />
        </label>
        <button type="submit" className="botao">
          Comparar
        </button>
      </form>

      {invertido1 && (
        <p className="comparacao-aviso">
          Aviso: no Período 1 a data de início é posterior à de fim. O intervalo
          não contém nenhum lançamento e a DRE sairá zerada.
        </p>
      )}
      {invertido2 && (
        <p className="comparacao-aviso">
          Aviso: no Período 2 a data de início é posterior à de fim. O intervalo
          não contém nenhum lançamento e a DRE sairá zerada.
        </p>
      )}
      {erro && <p className="erro">{erro}</p>}
      {carregando && <p>Carregando...</p>}
      {!carregando && !dados && !erro && (
        <p className="comparacao-vazio">
          Escolha os dois períodos e clique em Comparar.
        </p>
      )}

      {!carregando && dados && (
        <>
          <h3>Balanço Patrimonial</h3>
          <p className="comparacao-legenda">
            Foto acumulada até {formatarData(dados.p1.fim)} (Período 1) e até{" "}
            {formatarData(dados.p2.fim)} (Período 2).
          </p>
          {!dados.bp1.balanceado && (
            <p className="erro">
              Atenção: no Período 1 o Ativo ({fmt(dados.bp1.total_ativo)}) não
              bate com Passivo + PL ({fmt(dados.bp1.total_passivo_pl)}).
            </p>
          )}
          {!dados.bp2.balanceado && (
            <p className="erro">
              Atenção: no Período 2 o Ativo ({fmt(dados.bp2.total_ativo)}) não
              bate com Passivo + PL ({fmt(dados.bp2.total_passivo_pl)}).
            </p>
          )}

          <h4>Ativo</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasSecoes(dados.bp1.ativo, dados.bp2.ativo),
                linhaTotal(
                  "total-ativo",
                  "Total do Ativo",
                  dados.bp1.total_ativo,
                  dados.bp2.total_ativo
                ),
              ]}
            />
          </div>

          <h4>Passivo + Patrimônio Líquido</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasSecoes(dados.bp1.passivo_pl, dados.bp2.passivo_pl),
                linhaTotal(
                  "total-passivo-pl",
                  "Total do Passivo + PL",
                  dados.bp1.total_passivo_pl,
                  dados.bp2.total_passivo_pl
                ),
              ]}
            />
          </div>

          <h3>Demonstração de Resultado do Exercício</h3>
          <p className="comparacao-legenda">
            Fluxo de {formatarData(dados.p1.inicio)} a {formatarData(dados.p1.fim)}{" "}
            (Período 1) e de {formatarData(dados.p2.inicio)} a{" "}
            {formatarData(dados.p2.fim)} (Período 2).
          </p>

          <h4>Receitas</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasContas(dados.dre1.receitas, dados.dre2.receitas, "receita"),
                linhaTotal(
                  "total-receitas",
                  "Total de receitas",
                  dados.dre1.total_receitas,
                  dados.dre2.total_receitas
                ),
              ]}
            />
          </div>

          <h4>Despesas</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasContas(dados.dre1.despesas, dados.dre2.despesas, "despesa"),
                linhaTotal(
                  "total-despesas",
                  "Total de despesas",
                  dados.dre1.total_despesas,
                  dados.dre2.total_despesas
                ),
              ]}
            />
          </div>

          <h4>Resultado</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                linhaTotal(
                  "resultado-periodo",
                  "Resultado do período",
                  dados.dre1.resultado_periodo,
                  dados.dre2.resultado_periodo
                ),
              ]}
            />
          </div>
        </>
      )}
    </section>
  );
}
```

2. **Acrescente as classes novas a `frontend/src/index.css`.** Três edições,
   nesta ordem:

   **(a)** Acrescente `.comparacao-aviso` à regra de âmbar que já existe (hoje
   linhas 261–264), sem duplicar o literal da cor:

```css
/* Âmbar validado para contraste (≈6,8:1 sobre --papel); fora de escopo desta
   revisão, fica literal de propósito. */
.grafico-aviso,
.analise-nao-significativo,
.comparacao-aviso {
  color: #92400e;
}
```

   **(b)** Insira o bloco novo logo **depois** do bloco `/* ---- Análise ---- */`
   (ou seja, depois da regra `.analise-motivo`, hoje terminando na linha 409) e
   **antes** de `/* ---- telas estreitas ---- */`:

```css
/* ---- comparação entre períodos ----
   Duas colunas aqui significam TEMPO, não débito/crédito. Por isso nada de
   .bp-coluna: o fio vertical daquela classe é a marca da conta T e reutilizá-lo
   com outro sentido é justamente a inconsistência que a repaginação eliminou.
   A comparação vive dentro de uma tabela só — período 1, período 2 e variação
   como colunas irmãs de cada linha —, que é o que permite a coluna de variação
   existir. O sistema de pautas (fio de subtotal, fio duplo de total) é o mesmo
   das outras páginas, sem classe nova. */

.comparacao-intro {
  font-size: 13px;
  color: var(--tinta-fraca);
  max-width: 60ch;
}

.comparacao-form {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px 20px;
  align-items: end;
  margin-top: 16px;
}

/* O botão ocupa a faixa inteira abaixo dos quatro campos e encosta à esquerda
   — mesma leitura de .form-lancamento .botao. */
.comparacao-form .botao {
  grid-column: 1 / -1;
  justify-self: start;
}

.comparacao-legenda {
  font-size: 12px;
  color: var(--tinta-fraca);
  margin: 4px 0 0;
}

.comparacao-vazio {
  font-size: 13px;
  color: var(--tinta-fraca);
  margin-top: 24px;
}

/* Nome da conta é a coluna larga; as três de número ficam com o resto,
   iguais entre si e alinhadas à direita por .razao-valor. */
.comparacao-conta {
  width: 40%;
}
```

   **(c)** Dentro do `@media (max-width: 720px)` já existente, acrescente logo
   depois da regra `.form-lancamento { grid-template-columns: 1fr; }`:

```css
  .comparacao-form {
    grid-template-columns: 1fr;
  }
```

3. **Registre a aba em `frontend/src/App.jsx`.** Acrescente o import depois do
   de `Analise` e a entrada ao fim de `ABAS`:

```jsx
import Analise from "./pages/Analise";
import Comparacao from "./pages/Comparacao";

const ABAS = {
  lancamentos: { rotulo: "Lançamentos", componente: Lancamentos },
  balancete: { rotulo: "Balancete", componente: Balancete },
  bp: { rotulo: "Balanço Patrimonial", componente: BalancoPatrimonial },
  dre: { rotulo: "DRE", componente: DRE },
  analise: { rotulo: "Análise", componente: Analise },
  comparacao: { rotulo: "Comparação", componente: Comparacao },
};
```

   Nada mais em `App.jsx` muda: a aba inicial continua `"lancamentos"` e o
   `map` sobre `ABAS` já cobre a entrada nova.

4. **Rode o build:**

```
cd frontend && npm run build
```

   Esperado: build concluído sem erro. Se acusar `Comparacao is not defined` ou
   erro de importação, o passo 3 ficou incompleto.

5. **Confirme que nenhuma dependência entrou e que nenhuma página existente foi
   editada:**

```
git status --short frontend/src
git diff --stat frontend/package.json
```

   Esperado: `A frontend/src/pages/Comparacao.jsx`,
   `M frontend/src/App.jsx`, `M frontend/src/index.css` — e mais nada. O diff
   de `package.json` tem de vir vazio.

6. **Rode a suíte de backend uma última vez, para garantir que nada do
   frontend a afetou:**

```
cd backend && python -m pytest -q
```

   Esperado: `39 passed`.

7. **Commit:**

```
git add frontend/src/pages/Comparacao.jsx frontend/src/App.jsx frontend/src/index.css
git commit -m "Página de comparação entre períodos"
```

## Verificação no navegador (coordenador, depois da Tarefa 4)

Não é passo de nenhuma tarefa — o implementador não faz isto.

1. Com o backend rodando e a base semeada, abrir a aba "Comparação".
2. Comparar dois meses com movimento diferente e conferir: as duas colunas de
   BP fecham (`Total do Ativo` == `Total do Passivo + PL` em cada período), a
   DRE do período curto é menor que a acumulada, e a coluna de variação mostra
   `—` em toda linha cujo Período 1 esteja zerado.
3. Confirmar que nenhuma célula de variação imprime `-0,00%`, `Infinity%` ou
   `NaN%`.
4. Inverter as datas de um período e confirmar o aviso âmbar inline, com o
   botão "Comparar" ainda funcionando e o relatório saindo zerado.
5. Reabrir Balancete, Balanço Patrimonial, DRE e Análise e confirmar que
   continuam idênticas ao que eram.
6. Estreitar a janela abaixo de 720px e confirmar que o formulário empilha em
   uma coluna e as tabelas rolam na horizontal.
