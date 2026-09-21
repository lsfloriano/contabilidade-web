# Demonstração de Fluxo de Caixa (DFC) — design

## Objetivo

Terceira demonstração clássica, fechando o trio BP + DRE + DFC. Mostra as
entradas e saídas de caixa do período, agrupadas em três atividades
(operacional, investimento, financiamento), pelo **método direto** — construído
a partir dos lançamentos individuais que o app já guarda, e não por ajustes
sobre o resultado contábil (método indireto), que exigiria um mecanismo de
rastreio de saldo inicial/final por conta patrimonial que este app não tem
hoje.

## Fora de escopo

- **Método indireto.** Considerado e descartado: não se encaixa na arquitetura
  transacional do app sem um motor de ajustes novo.
- **Filtro de período.** Segue a mesma convenção de Balancete/BP/DRE antes da
  Comparação existir: sem filtro de data, acumula desde o primeiro lançamento.
  Se um dia a Comparação quiser incluir o DFC, isso é trabalho separado —
  mesma lição já aplicada a BP/DRE, que ganharam filtro depois, sob demanda.
- **Mudança no modelo de dados.** O plano de contas é fixo (semeado em
  `seed.py`, sem endpoint de criação/edição — confirmado antes de desenhar
  isto). A classificação por atividade é uma constante no backend, no mesmo
  espírito de `GRUPOS_ATIVO`/`GRUPOS_PASSIVO_PL` que já existem em
  `relatorios.py`, não uma coluna nova em `ContaContabil`.

## Classificação por atividade

Regra geral por `grupo`, com duas exceções pontuais por `codigo`:

| Atividade | Contas |
|---|---|
| Operacional | Clientes, Estoques (ativo circulante, exceto Caixa/Bancos); Fornecedores, Salários a Pagar, Impostos a Pagar (passivo circulante, exceto Empréstimos CP); toda conta de Receita; toda conta de Despesa (inclusive Despesas Financeiras — juros como operacional é a prática brasileira usual) |
| Investimento | Imobilizado, Investimentos (ativo não circulante) |
| Financiamento | **Empréstimos CP** e **Empréstimos LP** (exceção ao grupo — estão em Passivo Circulante/Não Circulante, mas são financiamento, não operacional); Capital Social, Lucros/Prejuízos Acumulados (patrimônio líquido) |
| Fora do DFC | Lançamento entre Caixa e Bancos (transferência interna — não é entrada nem saída real de caixa) |

Caixa (1.1.01) e Bancos (1.1.02) nunca aparecem como "contraparte" — são as
duas pontas que definem se um lançamento é ou não um movimento de caixa.

## Regra de inclusão de um lançamento

Para cada lançamento:

- Se **os dois lados** (débito e crédito) são Caixa ou Bancos → **fora do
  DFC** (transferência interna).
- Se **o débito** é Caixa ou Bancos (e o crédito não) → **entrada**; a
  contraparte é a conta de crédito, e ela decide a atividade.
- Se **o crédito** é Caixa ou Bancos (e o débito não) → **saída**; a
  contraparte é a conta de débito, e ela decide a atividade.
- Se **nenhum lado** é Caixa ou Bancos → **fora do DFC** (não é fluxo de
  caixa ainda — ex.: venda a prazo, que só vira caixa quando o cliente paga,
  num lançamento futuro separado).

Linhas são agrupadas por conta dentro de cada atividade (somando os
lançamentos daquela conta), no mesmo estilo do Balancete/DRE — nunca listando
lançamento a lançamento.

## A verificação de fechamento

Saldo inicial de caixa é sempre 0 — o app acumula desde o primeiro
lançamento, mesma convenção do BP e da DRE. A variação líquida é a soma de
todos os movimentos das três atividades. O saldo final deve bater com o saldo
de Caixa + Bancos que `calcular_balancete` já calcula.

Essa igualdade não é uma esperança, é uma prova por partida dobrada: excluir
os lançamentos Caixa↔Bancos do somatório não muda o total, porque um débito
em Caixa e crédito em Bancos (ou vice-versa) se cancelam exatamente na soma
Caixa+Bancos — a mesma propriedade que já sustenta `balanceado` no BP e
Σdébito=Σcrédito no Balancete, aplicada a um subconjunto diferente de contas.
Isso vira um teste formal (`Σmovimentos do DFC == saldo Caixa + saldo Bancos`),
não só uma afirmação em comentário.

A página mostra um aviso (mesmo padrão de `!bp.balanceado`) se a igualdade
falhar — o que, por construção, nunca deveria acontecer, mas é a mesma rede
de segurança que o BP já tem.

## Backend

Novo em `backend/app/relatorios.py`:

```python
CONTAS_CAIXA = {"1.1.01", "1.1.02"}  # Caixa, Bancos
CODIGOS_FINANCIAMENTO_DFC = {"2.1.02", "2.2.01"}  # Empréstimos CP, Empréstimos LP

def _categoria_dfc(conta: dict) -> str:
    if conta["codigo"] in CODIGOS_FINANCIAMENTO_DFC:
        return "financiamento"
    if conta["grupo"] == Grupo.ativo_nao_circulante.value:
        return "investimento"
    if conta["grupo"] == Grupo.patrimonio_liquido.value:
        return "financiamento"
    return "operacional"
```

`montar_dfc` itera os lançamentos brutos (não passa por `calcular_balancete`,
que agrupa por conta sem preservar qual lado é débito/crédito por
lançamento — aqui isso importa), classifica cada um pela regra acima, agrupa
por conta dentro de cada atividade, e separadamente chama
`calcular_balancete(db)` só para pegar o saldo de Caixa+Bancos e comparar —
são dois caminhos de cálculo independentes chegando (ou não) ao mesmo
número, que é o que faz do `confere` uma prova, não uma afirmação:

```python
def montar_dfc(db: Session) -> dict:
    lancamentos = db.query(Lancamento).all()
    contas = {c["codigo"]: c for c in _contas_dataframe(db).to_dict("records")}

    valores = {"operacional": {}, "investimento": {}, "financiamento": {}}
    for l in lancamentos:
        debito_e_caixa = l.conta_debito in CONTAS_CAIXA
        credito_e_caixa = l.conta_credito in CONTAS_CAIXA
        if debito_e_caixa and credito_e_caixa:
            continue  # transferência interna, não é fluxo de caixa
        if debito_e_caixa:
            contraparte = contas[l.conta_credito]
            valor = float(l.valor)  # entrada
        elif credito_e_caixa:
            contraparte = contas[l.conta_debito]
            valor = -float(l.valor)  # saída
        else:
            continue  # nenhum lado é caixa/bancos, ainda não é fluxo de caixa

        categoria = _categoria_dfc(contraparte)
        codigo = contraparte["codigo"]
        acumulado = valores[categoria].setdefault(
            codigo, {"nome": contraparte["nome"], "valor": 0.0}
        )
        acumulado["valor"] += valor

    def linhas(categoria):
        return [
            {"codigo": codigo, "nome": dado["nome"], "valor": dado["valor"]}
            for codigo, dado in valores[categoria].items()
        ]

    operacionais = linhas("operacional")
    investimentos = linhas("investimento")
    financiamentos = linhas("financiamento")

    subtotal_operacionais = sum(l["valor"] for l in operacionais)
    subtotal_investimentos = sum(l["valor"] for l in investimentos)
    subtotal_financiamentos = sum(l["valor"] for l in financiamentos)
    variacao_liquida = subtotal_operacionais + subtotal_investimentos + subtotal_financiamentos

    saldo_inicial = 0.0
    saldo_final = saldo_inicial + variacao_liquida

    balancete = calcular_balancete(db)
    saldo_caixa_bancos = sum(c["saldo"] for c in balancete if c["codigo"] in CONTAS_CAIXA)

    return {
        "operacionais": operacionais,
        "subtotal_operacionais": subtotal_operacionais,
        "investimentos": investimentos,
        "subtotal_investimentos": subtotal_investimentos,
        "financiamentos": financiamentos,
        "subtotal_financiamentos": subtotal_financiamentos,
        "variacao_liquida": variacao_liquida,
        "saldo_inicial": saldo_inicial,
        "saldo_final": saldo_final,
        # Mesma tolerância de 0.01 que já governa `balanceado` no BP — não é
        # um número novo, é o mesmo padrão de "ponto flutuante cru" do resto
        # do app aplicado aqui.
        "confere": abs(saldo_final - saldo_caixa_bancos) < 0.01,
    }
```

Novo endpoint `GET /relatorios/dfc` em `backend/app/routers/relatorios.py`,
novo schema `DFCReport` em `backend/app/schemas.py`, seguindo exatamente o
padrão de `montar_dre`/`DREReport`.

## Frontend

Sétima aba "DFC" em `App.jsx`, nova página `Dfc.jsx` seguindo o padrão de
`DRE.jsx`: três `<h4>` + tabela com `.razao-valor`/`classeValor`/`fmt` e linha
`.razao-subtotal` por atividade, fechando com `.razao-fechamento` mostrando
"Saldo inicial → Variação líquida → Saldo final", e um aviso `.erro` se
`!dfc.confere` (mesmo padrão do aviso de `!bp.balanceado`).

## Testes

Backend (pytest, padrão de `backend/tests/`):

- Um lançamento por atividade (operacional, investimento, financiamento),
  conferindo categoria e sinal.
- Uma transferência Caixa↔Bancos, confirmando que fica fora do DFC.
- Um lançamento sem nenhum lado em Caixa/Bancos (ex.: venda a prazo),
  confirmando que fica fora.
- O teste formal do fechamento: soma de todos os movimentos do DFC bate com
  saldo de Caixa + Bancos vindo de `calcular_balancete`, para um conjunto de
  lançamentos variados.
- Endpoint `/relatorios/dfc`.

Frontend: sem framework de teste, convenção já estabelecida do projeto.
Verificação visual pelo coordenador, no navegador.

## Arquivos afetados

- `backend/app/relatorios.py` — `montar_dfc`, `_categoria_dfc` (criar)
- `backend/app/schemas.py` — `DFCReport` (criar)
- `backend/app/routers/relatorios.py` — rota `/dfc` (modificar)
- `backend/tests/test_relatorios_dfc.py` (criar)
- `frontend/src/api.js` — `getDFC` (modificar)
- `frontend/src/pages/Dfc.jsx` (criar)
- `frontend/src/App.jsx` — nova entrada em `ABAS` (modificar)
