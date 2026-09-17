# Contabilidade Web — Design

**Data**: 2026-09-17
**Status**: Aprovado para implementação

## Objetivo

Projeto de portfólio/aprendizado que replica o ciclo contábil básico
(lançamento → razão/balancete → Balanço Patrimonial e DRE) como uma
aplicação web, combinando pandas (motor de cálculo) com uma API e um
front-end de verdade. Inspirado no conteúdo do curso "Curso de
Contabilidade para não contadores" (Iudícibus/Marion).

## Escopo (v1)

**Dentro do escopo:**
- Cadastro de lançamentos contábeis (partida dobrada simples: 1 conta
  debitada + 1 conta creditada por lançamento)
- Entrada manual (formulário) e em lote (upload de CSV)
- Plano de contas pré-definido e fixo
- Relatórios: Balancete, Balanço Patrimonial, DRE
- Período único contínuo (sem fechamento de exercício)

**Fora do escopo (explicitamente adiado):**
- Lançamentos compostos (múltiplas contas debitadas/creditadas num só lançamento)
- Fechamento de período / apuração de resultado com zeramento de contas
- DFC, DVA, análise de quocientes financeiros
- Plano de contas customizável pelo usuário
- Autenticação/multi-usuário — aplicação de uso local, single-user
- Testes automatizados de frontend

## Arquitetura

```
┌─────────────┐      JSON/HTTP       ┌──────────────┐      SQL      ┌──────────┐
│  React SPA  │ ───────────────────► │   FastAPI    │ ────────────► │  SQLite  │
│  (Vite)     │ ◄─────────────────── │  + pandas    │ ◄──────────── │          │
└─────────────┘                      └──────────────┘               └──────────┘
```

- **Backend**: FastAPI, SQLAlchemy (ORM sobre SQLite), pandas para todo
  cálculo de saldos e montagem dos relatórios.
- **Frontend**: React (Vite), sem SSR, consumindo a API via `fetch`.
  CORS liberado para o backend em desenvolvimento.
- Pandas nunca escreve no banco — ele só lê `lancamentos` +
  `plano_de_contas` para DataFrame e calcula os relatórios sob demanda
  (sem cache/materialização em v1).

## Modelo de dados

### `plano_de_contas` (seed fixo, populado na inicialização do banco)

| Campo | Tipo | Notas |
|---|---|---|
| codigo | string (PK) | ex: "1.1.01" |
| nome | string | ex: "Caixa" |
| natureza | enum | `devedora` \| `credora` |
| grupo | enum | ver tabela abaixo |
| tipo | enum | `patrimonial` (vai pro BP) \| `resultado` (vai pra DRE) |

Grupos e naturezas:

| Grupo | Tipo | Natureza |
|---|---|---|
| Ativo Circulante | patrimonial | devedora |
| Ativo Não Circulante | patrimonial | devedora |
| Passivo Circulante | patrimonial | credora |
| Passivo Não Circulante | patrimonial | credora |
| Patrimônio Líquido | patrimonial | credora |
| Receita | resultado | credora |
| Despesa | resultado | devedora |

Plano de contas padrão (seed):

- **Ativo Circulante**: Caixa, Bancos, Clientes, Estoques
- **Ativo Não Circulante**: Imobilizado, Investimentos
- **Passivo Circulante**: Fornecedores, Empréstimos CP, Salários a Pagar, Impostos a Pagar
- **Passivo Não Circulante**: Empréstimos LP
- **Patrimônio Líquido**: Capital Social, Lucros/Prejuízos Acumulados
- **Receita**: Receita de Vendas, Receita de Serviços
- **Despesa**: CMV, Despesas Administrativas, Despesas com Vendas, Despesas Financeiras, Impostos sobre Vendas

### `lancamentos`

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK, autoincrement) | |
| data | date | |
| conta_debito | string (FK → plano_de_contas.codigo) | |
| conta_credito | string (FK → plano_de_contas.codigo) | |
| valor | decimal | > 0 |
| historico | string (opcional) | descrição livre |

**Validações** (aplicadas tanto no formulário quanto no upload CSV):
- `conta_debito` e `conta_credito` devem existir no plano de contas
- `conta_debito != conta_credito`
- `valor > 0`
- `data` obrigatória e válida

## Cálculo dos relatórios (pandas)

1. Carrega `lancamentos` e `plano_de_contas` em DataFrames; funde (`merge`) lançamentos com o plano de contas duas vezes (uma para a conta de débito, outra para a de crédito).
2. "Explode" cada lançamento em dois movimentos (débito e crédito), monta um DataFrame único de movimentos por conta.
3. Agrupa por conta (`groupby`) somando débitos e créditos.
4. Saldo por conta:
   - Natureza devedora: `saldo = total_debito - total_credito`
   - Natureza credora: `saldo = total_credito - total_debito`
5. **Balancete**: tabela `conta | total_debito | total_credito | saldo`.
6. **BP**: filtra contas `tipo == patrimonial`, agrupa por `grupo`, soma saldos, monta estrutura Ativo (Circulante + Não Circulante) vs Passivo (Circulante + Não Circulante) + PL. Inclui um total de conferência (Ativo == Passivo + PL); se não bater, é sinal de bug e deve aparecer sinalizado na resposta da API.
7. **DRE**: filtra contas `tipo == resultado`, soma Receitas − Despesas = Resultado do Período.

## API (FastAPI)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/contas` | Lista o plano de contas |
| GET | `/lancamentos` | Lista lançamentos (ordenados por data) |
| POST | `/lancamentos` | Cria um lançamento manual. 422 se validação falhar |
| POST | `/lancamentos/upload` | Recebe CSV (`data,conta_debito,conta_credito,valor,historico`). Processa linha a linha com pandas; retorna `{inseridos: N, erros: [{linha, motivo}]}` — linhas válidas são inseridas mesmo se outras falharem |
| GET | `/relatorios/balancete` | Retorna o balancete |
| GET | `/relatorios/bp` | Retorna o Balanço Patrimonial estruturado |
| GET | `/relatorios/dre` | Retorna a DRE estruturada |

## Frontend (React)

- **Lançamentos**: formulário (data, conta débito, conta crédito — selects populados via `/contas`, valor, histórico) + botão de upload CSV com feedback de erros por linha + tabela dos lançamentos existentes.
- **Balancete**: tabela simples de saldos.
- **Balanço Patrimonial**: layout de duas colunas (Ativo | Passivo + PL), com subtotais por grupo e total geral.
- **DRE**: lista em cascata (Receita → Despesas por tipo → Resultado do Período), destacando lucro/prejuízo.

Navegação simples entre as 4 páginas (sem necessidade de rota complexa — pode ser tabs ou react-router básico).

## Tratamento de erros

- Backend retorna `422` com corpo detalhando o campo inválido para erros de validação de lançamento manual (aproveitando a validação nativa do FastAPI/Pydantic).
- Upload de CSV nunca falha a operação inteira por causa de uma linha ruim — processa o que é válido e reporta o resto, para ficar didático sobre *o que* deu errado.
- Se o total do BP não fechar (Ativo ≠ Passivo + PL) — o que só deveria acontecer por bug, já que cada lançamento é uma partida dobrada balanceada — a API retorna o relatório mesmo assim, com um campo `balanceado: false`, para não esconder o problema.

## Testes

- **Backend (pytest)**:
  - Cálculo de saldo por conta (devedora e credora) com múltiplos lançamentos
  - Montagem do BP (grupos corretos, Ativo = Passivo + PL)
  - Montagem da DRE (Receita − Despesa = Resultado)
  - Validação de lançamento (conta inexistente, débito == crédito, valor <= 0)
  - Upload de CSV com linhas mistas (válidas + inválidas)
  - Endpoints via `TestClient` (happy path + validação)
- **Frontend**: nenhum teste automatizado em v1 (decisão consciente de escopo); verificação manual no navegador antes de considerar cada página pronta.

## Estrutura de pastas proposta

```
contabilidade-web/
  backend/
    app/
      main.py          # FastAPI app, CORS, rotas
      models.py         # SQLAlchemy models
      schemas.py        # Pydantic schemas
      db.py              # engine/session, seed do plano de contas
      relatorios.py     # lógica pandas (balancete/BP/DRE)
    tests/
    requirements.txt
  frontend/
    src/
      pages/ (Lancamentos, Balancete, BalancoPatrimonial, DRE)
      api.js
    package.json
  docs/superpowers/specs/
    2026-09-17-contabilidade-web-design.md
```
