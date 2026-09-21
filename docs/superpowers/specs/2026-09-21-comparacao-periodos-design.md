# Comparação entre períodos — design

## Objetivo

Hoje nenhum relatório do app filtra por data: Balancete, BP, DRE e Análise
somam todos os lançamentos da base, sempre. Este trabalho adiciona uma tela
nova que compara dois períodos — Balanço Patrimonial e DRE de cada um, lado a
lado, com variação percentual — sem mudar o modelo de dados e sem alterar o
comportamento das quatro páginas existentes, que continuam mostrando tudo,
sem filtro.

## Fora de escopo

- **Encerramento de exercício de verdade.** Zerar contas de resultado,
  apurar e transferir pro PL, abrir o próximo período com saldos carregados —
  isso exigiria um conceito real de "exercício" no modelo e um lançamento de
  encerramento no banco. Considerado e descartado nesta rodada: o pedido do
  usuário é comparar períodos, não simular o fechamento contábil.
- **Balancete e Análise na comparação.** A tela nova mostra só BP e DRE.
  Balancete fica de fora porque não foi pedido; Análise fica de fora porque
  mistura dado de foto (BP) com dado de fluxo (DRE) em fórmulas que já são as
  mais delicadas do app (ver os comentários de `_indicador` e as observações
  de ROA/ROE/margem em `relatorios.py`) — dobrar esse cuidado para dois
  cálculos independentes é trabalho separado.
- **Filtro nas quatro páginas existentes.** Lançamentos, Balancete, BP e DRE
  continuam sem seletor de data. Só a tela nova filtra.

## Modelo de dados

Nenhuma mudança. `Lancamento.data` já existe e já é o suficiente — filtrar é
uma questão de consulta, não de schema.

## Backend: BP é foto, DRE é fluxo

Essa distinção decide a forma do filtro, e é a parte do design que não pode
ficar ambígua:

- **Balanço Patrimonial é uma foto na data X** — saldo acumulado desde a
  fundação da empresa até aquela data. Comparar dois períodos = duas datas de
  corte, cada uma somando *tudo* desde o início até ali.
- **DRE é fluxo** — receitas e despesas que ocorreram *dentro* de um
  intervalo. Vale registrar o que a leitura do código atual revelou: a DRE de
  hoje na verdade não filtra por período nenhum — sem um mecanismo de
  encerramento de exercício, as contas de resultado acumulam desde o início
  dos tempos, e isso já está documentado como simplificação deliberada no
  comentário do ROE ("este app trabalha com um período contínuo único"). O
  filtro de intervalo que este trabalho adiciona é o que torna a DRE uma DRE
  de verdade pela primeira vez — mas só quando o parâmetro é passado; sem
  ele, o comportamento atual (o período contínuo único) continua idêntico.

### Mudanças em `relatorios.py`

`calcular_balancete` ganha dois parâmetros opcionais, `None` por padrão:

```python
def calcular_balancete(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[dict]:
```

O filtro entra em `_lancamentos_dataframe` (ou como filtro aplicado ao
DataFrame logo depois de montá-lo): `data >= data_inicio` quando fornecido,
`data <= data_fim` quando fornecido. Com os dois `None`, o resultado é
byte-idêntico ao de hoje — é o que garante zero regressão nas quatro páginas
existentes, e é testado explicitamente (ver Testes).

```python
def montar_bp(db: Session, data_corte: date | None = None) -> dict:
    balancete = calcular_balancete(db, data_fim=data_corte)
    ...

def montar_dre(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> dict:
    balancete = calcular_balancete(db, data_inicio=data_inicio, data_fim=data_fim)
    ...
```

`montar_analise` não muda — fica de fora do escopo, então continua chamando
`calcular_balancete(db)` sem argumentos.

### Uma propriedade que a torna simples

`calcular_balancete` sempre itera o plano de contas inteiro (as mesmas 20
contas), independente do filtro — uma conta sem lançamento no recorte
aparece com saldo 0.0, nunca some da lista. Os dois períodos de uma
comparação **sempre têm as mesmas linhas, na mesma ordem**. Isso elimina por
construção o caso "conta existe num período e não no outro", que normalmente
seria a parte chata de qualquer comparação por código de conta.

Vale confirmar também que `balanceado` (`abs(total_ativo - total_passivo_pl)
< 0.01`) continua válido para qualquer `data_corte`, não só para "hoje": a
propriedade vem de somar o resultado não realizado ao PL (a linha sintética
`RESULTADO` que `montar_bp` já injeta), e essa soma fecha a equação
patrimonial para **qualquer** subconjunto de lançamentos, não só para o
conjunto completo — é a mesma invariante de partida dobrada que já sustenta
o Balancete, aplicada a um corte de data em vez de a uma partição qualquer.
Nenhum código novo precisa reforçar isso; é consequência do que já existe.

## Endpoints

Os dois endpoints existentes ganham query params opcionais — nenhum schema
novo, `BPReport`/`DREReport` não mudam de forma:

```
GET /relatorios/bp                              (como hoje)
GET /relatorios/bp?data_corte=2026-09-30

GET /relatorios/dre                             (como hoje)
GET /relatorios/dre?data_inicio=2026-09-01&data_fim=2026-09-30
```

Sem endpoint combinado de comparação. A tela nova dispara 4 chamadas (BP × 2
períodos, DRE × 2 períodos) reaproveitando `getBP`/`getDRE` do frontend com
um argumento a mais — mantém cada peça pequena e testável isoladamente, em
vez de um novo schema de resposta combinada.

## Frontend: página "Comparação"

Nova aba em `App.jsx` (padrão idêntico às cinco existentes — o roteamento é
um `useState` com um dicionário `ABAS`, sem biblioteca de rotas).

Dois seletores de período, cada um com dois `<input type="date">` (início e
fim), nos mesmos moldes do formulário de Lançamentos — **4 campos de data no
total, não 6**: a data de "fim" de cada período alimenta as duas chamadas
daquele período — é o `data_corte` do BP **e** o `data_fim` da DRE ao mesmo
tempo. A data de "início" alimenta só a DRE (`data_inicio`); o BP não tem
início, por definição (é sempre "desde a fundação"). Não existe um campo
separado de "data de corte do BP" — usar o mesmo "fim" para os dois é a
própria ideia de "o Balanço de fim de setembro junto com a DRE de setembro".

Botão "Comparar". Ao clicar: as 4 chamadas em paralelo (`getBP(p1Fim)`,
`getBP(p2Fim)`, `getDRE(p1Inicio, p1Fim)`, `getDRE(p2Inicio, p2Fim)`), depois
BP dos dois períodos lado a lado e DRE dos dois períodos lado a lado, cada
linha com uma coluna de variação %.

**O layout de duas colunas não reaproveita a classe da conta T do BP**
(`.bp-coluna`, cujo fio vertical significa especificamente débito/crédito).
Aqui duas colunas significam **tempo**, um eixo diferente — usar a mesma
marca visual para dois significados diferentes é a inconsistência que o
trabalho de repaginação anterior existiu para eliminar. Classes novas,
próprias desta página, ainda que o layout de grade pareça superficialmente
parecido.

### Variação percentual — calculada no frontend

`(valor2 - valor1) / Math.abs(valor1)`, a partir dos dois JSONs já corretos
vindos do backend. É aritmética de exibição — mesma categoria de `fmt`/
`classeValor`, não lógica contábil nova — não uma recomputação de saldo ou
resultado.

Regras de borda:

- **`valor1 === 0`**: divisão não existe, mostra "—" em vez de `Infinity%`
  ou de um erro.
- **`valor1` negativo** (ex.: prejuízo diminuindo): a fórmula já está
  correta aqui, ao contrário do problema que a página de Análise teve com
  denominador negativo. Lá numerador e denominador são grandezas diferentes
  (ex.: resultado / PL) e a divisão por um denominador negativo inverte o
  sinal de um jeito que engana. Aqui `valor1` e `valor2` são a **mesma
  grandeza em dois instantes**, e dividir por `|valor1|` (não por `valor1`)
  é exatamente o que evita a inversão: resultado indo de −1000 para −500
  (prejuízo menor, ou seja, melhora) dá `(−500 − (−1000)) / 1000 = +50%`,
  que lê certo. Não precisa do aviso de "não significativo" que `_indicador`
  usa.
- **Início > fim num período**: não validado no backend — um intervalo
  invertido não bate com nenhuma linha (`data >= início AND data <= fim`
  vazio) e o relatório sai zerado, sem erro. Aviso inline no frontend se
  início > fim, sem travar o botão "Comparar".
- **Contas zeradas no período**: esperado, não é caso de erro — muitas
  linhas provavelmente zeram num recorte curto.

## Testes

Backend (pytest, seguindo o padrão de `backend/tests/`):

- `calcular_balancete`/`montar_bp`/`montar_dre` **sem** os novos parâmetros
  continuam produzindo exatamente o que produzem hoje — regressão explícita,
  não assumida.
- Filtro por intervalo exclui lançamentos fora dele (um lançamento antes do
  início, um depois do fim, um dentro — só o do meio conta).
- `montar_bp` com `data_corte` soma só até a data, inclusive.
- Endpoints: `client.get("/relatorios/bp?data_corte=...")` e o equivalente
  para `/dre` com os dois parâmetros.

Frontend: sem framework de teste, convenção já estabelecida no projeto. A
variação % é conferida na mão durante a implementação (mesmo método usado
para `formatarData`), e a tela é verificada no navegador pelo coordenador.

## Arquivos afetados

- `backend/app/relatorios.py` — `calcular_balancete`, `montar_bp`,
  `montar_dre` (modificar)
- `backend/app/routers/relatorios.py` — query params nos dois endpoints
  (modificar)
- `backend/tests/test_relatorios_bp.py`, `test_relatorios_dre.py` — testes
  novos de filtro (modificar)
- `frontend/src/api.js` — `getBP`/`getDRE` aceitam argumentos opcionais
  (modificar)
- `frontend/src/pages/Comparacao.jsx` — página nova (criar)
- `frontend/src/App.jsx` — nova entrada em `ABAS` (modificar)
- `frontend/src/index.css` — classes da página nova (modificar)
