# Convenção do razão — repaginação visual do frontend

Plano de implementação — branch `feat/ui-razao` (partiu de `master`).

## Objetivo

Unificar a linguagem visual do app em torno da **convenção tipográfica da
contabilidade** — o sistema de pautas (fios) — em vez de cromo aplicado
(cartões, sombras, cantos arredondados uniformes).

Quatro defeitos observados que este plano corrige:

1. O formulário de Lançamentos é uma linha corrida de rótulo+campo inline que
   quebra no meio.
2. Dinheiro nas tabelas usa `.toFixed(2)` → `79750.00`, alinhado à esquerda, sem
   separador de milhar, enquanto os gráficos e a página de Análise usam `Intl`
   pt-BR → `79.750,00`. O mesmo número aparece de duas formas na mesma tela.
3. As páginas novas (Análise, cartões de gráfico) estabeleceram uma linguagem
   visual que as três páginas de tabela mais antigas nunca adotaram.
4. `frontend/index.html` não tem `<meta name="viewport">`, então celulares
   renderizam a ~980px.

**Este trabalho é só visual e só frontend.** O backend não é tocado.

## Restrições globais (valem para todas as tarefas)

- **Backend fora de escopo.** Nenhum arquivo de `backend/` é lido, editado ou
  criado. Os 27 testes pytest existentes continuam passando porque nada muda lá.
- **Não altere comportamento.** Nenhum cálculo novo, nenhuma chamada de API
  nova ou alterada, nenhuma mudança de lógica de componente além do que a
  reestruturação de markup exige (trocar `<p>` por `<p>` com dois `<span>`,
  envolver tabela em `<div>`, trocar `toFixed` por `fmt`). Nenhum `useState`,
  `useEffect`, handler ou import de `../api` muda em qualquer tarefa.
- **Zero dependências novas.** `frontend/package.json` não muda. **Nenhum link
  de webfont** — o app é local-first e uma requisição externa de fonte quebraria
  o uso offline.
- **Somente tema claro.** `frontend/src/index.css` não tem nenhuma regra
  `prefers-color-scheme`, de propósito. Não adicione nenhuma.
- **Não quebre os tratamentos `aviso` / `observacao` / `não-significativo`.**
  As classes `.grafico-aviso`, `.analise-nao-significativo`,
  `.analise-observacao`, `.analise-motivo` e os parágrafos que as usam carregam
  semântica deliberada de recusa a enganar (PL negativo, CMV negativo,
  denominador zero). O âmbar `#92400e` **não muda** e continua literal no CSS.
- **Todas as strings visíveis em português (pt-BR).**
- **Sem testes automatizados de frontend.** Decisão de escopo deliberada e
  documentada do projeto. Não adicione Vitest/Jest/Testing Library. O **portão
  automatizado de toda tarefa é `npm run build` passando a partir de
  `frontend/`**. A verificação no navegador é feita depois, pelo **coordenador**
  — não pelo implementador da tarefa. Nenhuma tarefa deste plano pede ao
  implementador que abra o navegador.
- **Estilo existente:** componentes de função, hooks, sem framework de CSS,
  `className` em strings simples.

## Decisões de design já fechadas (não reabrir)

**Não envolva as tabelas em cartões.** Um rascunho anterior propôs exatamente
isso e foi rejeitado: cartões arredondados uniformes com um `border-radius` e
uma sombra cinza suave são marca registrada documentada de design gerado. **O
dispositivo estrutural aqui é o fio (a pauta), não a caixa.**

A mesma regra vale para os dois lugares onde o app ainda usa caixa, e as duas
decisões são do coordenador:

- **A barra de abas vira papel com sublinhado de tinta na aba ativa.** As lajes
  `#1f2937`/`#374151` saem: laje escura é exatamente o cromo aplicado que esta
  repaginação existe para remover, e sublinhado é o vocabulário da pauta. A aba
  ativa **não** ganha caixa, nem fundo, nem canto arredondado — só o fio.
- **O cartão dos gráficos é removido.** Com o corpo e o cartão na mesma
  superfície, o contorno vira contorno puro, sem função; e manter um elemento em
  caixa enquanto todo o resto é pautado é a incoerência que este trabalho
  elimina. No lugar da borda e do raio, **um fio acima do bloco do gráfico**,
  como divisor de seção, na mesma pauta das tabelas. O SVG em si não muda —
  nenhuma coordenada, nenhum `fill`, nenhuma constante de geometria.
  **É reversível numa regra de CSS** e é a mudança cujo efeito o coordenador
  mais quer julgar no navegador: sem a caixa o gráfico pode ficar solto. Se
  ficar, o contorno volta trocando uma declaração (ver Tarefa 1, passo 4).

**Tipografia continua na pilha de sistema nesta rodada.** Uma serifada
auto-hospedada para o corpo do relatório foi considerada e **deliberadamente
adiada**. Não a re-adicione. O que muda na tipografia é apenas:
`font-variant-numeric: tabular-nums` em toda figura monetária, e a **remoção da
face monoespaçada** da linha de substituição da Análise (monoespaçado para
rótulos pequenos de dados é outro tell nomeado; algarismos tabulares na face
proporcional resolvem o alinhamento sem ele).

**Sinal de negativo:** mantenha o hífen que `Intl.NumberFormat("pt-BR")` emite.
**Não** troque por parênteses — a página de Análise já usa o hífen e mudar de
convenção no meio do app é pior do que escolher uma.

### Paleta — 6 tokens

| token | hex | papel |
|---|---|---|
| `--papel` | `#fcfcfb` | superfície única, em toda parte |
| `--tinta` | `#1a2233` | texto primário — tinta de razão azul-preta |
| `--tinta-fraca` | `#5a6472` | rótulos, texto secundário |
| `--pauta` | `#c8cdd6` | os fios — o elemento estrutural |
| `--pauta-fraca` | `#e3e6eb` | fio subordinado — só o conector da cascata da DRE |
| `--vermelho` | `#a4243b` | valores negativos e recusas, só |

Três coisas para o revisor verificar em vez de assumir:

- **A unificação da superfície tem razão técnica, não só estética.** O app hoje
  mistura `#f5f5f5` (frio, no `body`) com `#fcfcfb` (quente, nos cartões de
  gráfico). A paleta de cores dos gráficos foi validada para contraste
  **especificamente contra `#fcfcfb`**. Adotar essa superfície em toda parte
  **preserva** a validação em vez de invalidá-la.
- **`#0b0b0b` sai porque é um tell nomeado** na orientação de design ("quase
  preto tingido fazendo as vezes de preto"). `#1a2233` sobre `#fcfcfb` dá
  contraste ≈ **15,3:1**; `#5a6472` sobre `#fcfcfb` dá ≈ **5,8:1**; `#a4243b`
  sobre `#fcfcfb` dá ≈ **7,0:1**; o âmbar `#92400e` sobre `#fcfcfb` dá ≈
  **6,8:1** (era 6,5:1 sobre `#f5f5f5`, ou seja, melhora). Todos acima de
  4,5:1. Se o revisor quiser conferir, são contrastes WCAG 2.x calculados da
  luminância relativa.

- **O sexto token é decisão do coordenador, não deriva do design.** O design
  fechou em cinco. `--pauta-fraca` foi acrescentado para o fio conector da
  cascata da DRE (`COR_CONECTOR`, hoje `#e1e0d9`): ele **precisa** ser mais leve
  que o eixo, senão perde a subordinação, mas `#e1e0d9` é cinza quente numa
  paleta que passou a ser fria-neutra e os dois destoam lado a lado. `#e3e6eb`
  mantém as duas coisas. É fio, não texto, então não há piso WCAG a cumprir;
  contra `--papel` dá ≈1,21:1, praticamente o mesmo peso visual do `#e1e0d9` que
  substitui (≈1,19:1), e continua claramente abaixo do eixo `--pauta`
  (≈1,60:1). Se no navegador o conector sumir, é este token que se ajusta — e
  só ele.

**As cores de dado dos gráficos (`#2a78d6`, `#eb6834`, `#1baf7a`, `#eda100`,
`#e87ba4`, a divergente `#e34948`) e o âmbar `#92400e` NÃO mudam.** Foram
validadas para contraste e estão fora de escopo. Nenhuma tarefa as toca.

Também **não muda** a constante local `SUPERFICIE = "#fcfcfb"` em
`GraficoBalanco.jsx`: ela pinta os vãos entre segmentos empilhados e precisa ser
exatamente a cor da superfície — que agora é literalmente `--papel`. Continua
correta depois da Tarefa 1, quando o bloco do gráfico deixa de ter fundo próprio:
o que fica atrás do SVG passa a ser o `body`, também `--papel`. Deixe como está;
não a converta em variável CSS (é atributo `fill` de SVG).

### O sistema de pautas — o núcleo deste trabalho

Convenção tipográfica contábil, que também é "estrutura que codifica
informação":

- fio de cabelo entre linhas
- **fio simples acima de um subtotal**
- **fio duplo abaixo de um total final**
- nomes de conta à esquerda, todo dinheiro à direita com algarismos tabulares

```
Conta                        Total débito   Total crédito        Saldo
──────────────────────────────────────────────────────────────────────
1.1.01   Caixa                  50.000,00       12.000,00    38.000,00
1.1.02   Bancos                  8.000,00            0,00     8.000,00
──────────────────────────────────────────────────────────────────────
Subtotal                        58.000,00       12.000,00    46.000,00
══════════════════════════════════════════════════════════════════════
```

Tradução para CSS, com três pesos distinguíveis e **sem ambiguidade de
`border-collapse`** (na colapsagem, a borda mais larga vence):

| papel | CSS | largura |
|---|---|---|
| fio de cabelo entre linhas | `border-bottom: 1px solid var(--pauta)` em `td`/`th` | 1px |
| fio do cabeçalho | `border-bottom: 1px solid var(--tinta)` em `thead th` | 1px (não colide: a borda de cima da 1ª linha do corpo é `none`) |
| fio simples de subtotal | `border-top: 2px solid var(--tinta)` | 2px — vence o fio de cabelo de 1px da linha acima |
| fio duplo de total final | `border-bottom: 3px double var(--tinta)` | 3px — `double` precisa de ≥3px para renderizar duas linhas |

No Balanço Patrimonial, um **fio vertical entre as duas colunas** — é a
conta T, expressando a dualidade débito/crédito estruturalmente em vez de com um
rótulo:

```
Ativo                          │  Passivo + Patrimônio Líquido
                               │
Ativo Circulante               │  Passivo Circulante
  Caixa             4.510,00   │    Fornecedores         5.010,00
  Bancos           52.250,00   │    Empréstimos CP      20.000,00
  ──────────────────────────   │    ─────────────────────────────
  Subtotal         71.770,00   │    Subtotal            34.010,00
                               │
Total              79.760,00   │  Total                 79.760,00
══════════════════════════     │  ═══════════════════════════════
```

### O formulário — grade, rótulo acima do campo

```
Data              Conta débito                Conta crédito
[ 01/09/2026 ]    [ 1.1.01 — Caixa      ▾]    [ 2.3.01 — Capital ▾]

Valor             Histórico
[     1.000,00]   [ Integralização de capital        ]   [ Lançar ]
```

Com `grid-template-columns: repeat(3, 1fr)` e os seis filhos na ordem Data,
Conta débito, Conta crédito, Valor, Histórico, botão, esse arranjo sai sozinho —
o botão cai na coluna 3 da linha 2. Colapsa para uma coluna em telas estreitas.

### Formato único de número

Toda figura monetária do app passa pelo `fmt` existente de
`frontend/src/components/graficos-comuns.js`. **Nenhum `.toFixed(2)` em lugar
nenhum** ao fim do plano. São 14 ocorrências hoje: 1 em `Lancamentos.jsx`, 3 em
`Balancete.jsx`, 5 em `BalancoPatrimonial.jsx`, 5 em `DRE.jsx`.

### Princípios que o plano preserva

- O fio, não a caixa, é o dispositivo estrutural.
- Fio duplo significa final; fio simples significa subtotal — a pauta carrega a
  hierarquia.
- Vermelho é reservado a valores negativos e recusas; nada mais é colorido.
- A ousadia é gasta em um lugar só: o fio da conta T no Balanço.

## Contrato de nomes de classe (o mesmo em todas as tarefas)

Cada implementador vê só a sua tarefa. Estes nomes são contrato; não invente
variantes, não renomeie.

| nome | onde é definido | o que é |
|---|---|---|
| `--papel` `--tinta` `--tinta-fraca` `--pauta` `--pauta-fraca` `--vermelho` | Tarefa 1, `:root` | tokens de cor |
| `.razao-valor` | Tarefa 1 | célula/trecho de dinheiro: direita, `tabular-nums`, `nowrap` |
| `.valor-negativo` | Tarefa 1 | `color: var(--vermelho)`, usada **junto** com `.razao-valor` |
| `.razao-subtotal` | Tarefa 1 | `<tr>` de subtotal: fio simples acima, semibold |
| `.razao-fechamento` | Tarefa 1 | linha de total final **fora** de tabela: fio simples acima + fio duplo abaixo |
| `.tabela-rolagem` | Tarefa 1 | `<div>` que envolve tabela larga, `overflow-x: auto` |
| `.form-lancamento` `.campo` `.campo-rotulo` `.botao` | Tarefa 1 | grade do formulário |
| `.bp-colunas` `.bp-coluna` | Tarefa 1 | conta T do Balanço |
| `classeValor(valor)` | Tarefa 1, `graficos-comuns.js` | retorna `"razao-valor"` ou `"razao-valor valor-negativo"` |

Classes existentes que **continuam existindo com o mesmo nome**: `.erro`,
`.tabs`, `.tab`, `.tab-ativa`, `.grafico`, `.grafico-bp`, `.grafico-dre`,
`.grafico-subtitulo`, `.grafico-legenda`, `.grafico-legenda-cor`,
`.grafico-vazio`, `.grafico-aviso`, `.analise-*`, `.sr-only`.

Classe que **desaparece ao fim do plano**: `.total-linha`. A Tarefa 1 a mantém
temporariamente (para nenhuma tarefa intermediária deixar a tela quebrada) e a
**Tarefa 6 a remove**.

---

# Tarefa 1 — Fundação: tokens, sistema de pautas, viewport e tinta dos gráficos

Define o vocabulário visual inteiro de uma vez. Nenhuma página é alterada nesta
tarefa; as cinco tarefas seguintes implementam contra este vocabulário.

### Arquivos

- `frontend/src/index.css` — **Modificar** (substituição integral do conteúdo)
- `frontend/index.html` — **Modificar** (uma linha)
- `frontend/src/components/graficos-comuns.js` — **Modificar** (4 constantes + 1
  função nova + comentário de cabeçalho)
- `frontend/src/components/GraficoDRE.jsx` — **Modificar** (uma constante de cor,
  uma linha)

### Interfaces

**Consome:** nada (primeira tarefa).

**Produz** — tudo o que as Tarefas 2–6 usam:

- Variáveis CSS em `:root`: `--papel`, `--tinta`, `--tinta-fraca`, `--pauta`,
  `--pauta-fraca`, `--vermelho`.
- Classes CSS: `.razao-valor`, `.valor-negativo`, `.razao-subtotal`,
  `.razao-fechamento`, `.tabela-rolagem`, `.form-lancamento`, `.campo`,
  `.campo-rotulo`, `.botao`, `.bp-colunas`, `.bp-coluna`.
- Estilo global de tabela: `table`, `th, td`, `thead th` já trazem o fio de
  cabelo e o fio de cabeçalho. **Nenhuma página precisa de uma classe na tag
  `<table>`** — toda tabela do app é um razão.
- Export novo de `frontend/src/components/graficos-comuns.js`:
  ```js
  export function classeValor(valor: number): string
  ```
  Retorna `"razao-valor"` quando `valor >= 0` (ou `NaN`), e
  `"razao-valor valor-negativo"` quando `valor < 0`. Assinatura de um argumento
  só; nenhuma tarefa passa um segundo.
- Exports já existentes de `graficos-comuns.js`, inalterados em nome e
  assinatura: `fmt(valor)`, `BAR_W`, `RAIO`, `MENSAGEM_VAZIO`, `caminhoBarra`,
  `COR_EIXO`, `COR_TEXTO`, `COR_TEXTO_SEC`, `COR_TEXTO_MUDO` (os quatro últimos
  mudam de **valor**, não de nome).

### Passos

**1. Adicionar a meta viewport em `frontend/index.html`.**

O arquivo inteiro passa a ser:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Contabilidade Web</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**2. Atualizar as constantes de tinta e adicionar `classeValor` em
`frontend/src/components/graficos-comuns.js`.**

Substitua o bloco de comentário do topo e as quatro constantes de cor (linhas 1
a 12 do arquivo atual) por:

```js
// Vocabulário compartilhado de apresentação: formatação de número, cores de
// chrome/tinta, geometria de barra e a classe de valor monetário. Os gráficos de
// BP e DRE usam as cores e a geometria; as cinco páginas usam `fmt` e
// `classeValor`. Não abstrai a estrutura dos gráficos em si — cada um mantém seu
// próprio layout, eixos e legenda.

export const BAR_W = 24;
export const RAIO = 4;

// Tinta alinhada à paleta do index.css: texto do gráfico e texto da
// tabela precisam ser a mesma cor. COR_EIXO é o fio (--pauta).
export const COR_EIXO = "#c8cdd6";
export const COR_TEXTO = "#1a2233";
export const COR_TEXTO_SEC = "#5a6472";
export const COR_TEXTO_MUDO = "#5a6472";
```

Não toque em mais nada do arquivo: `formatador`, `fmt`, `MENSAGEM_VAZIO` e
`caminhoBarra` ficam byte a byte como estão.

Acrescente ao **fim** do arquivo:

```js
// Vermelho é reservado a valores negativos e recusas. Toda célula de dinheiro
// passa por aqui, inclusive as que nunca deveriam ser negativas: se um negativo
// aparecer onde não se esperava, ele aparece em vermelho em vez de passar
// despercebido.
export function classeValor(valor) {
  return valor < 0 ? "razao-valor valor-negativo" : "razao-valor";
}
```

**3. Apontar o fio conector da cascata para o token novo em
`frontend/src/components/GraficoDRE.jsx`.**

Uma linha, na faixa de constantes do topo do arquivo. Troque:

```js
const COR_CONECTOR = "#e1e0d9";
```

por:

```js
// --pauta-fraca do index.css: mais leve que o eixo de propósito — o conector é
// subordinado a ele — mas frio-neutro como o resto da paleta.
const COR_CONECTOR = "#e3e6eb";
```

**Não toque em `COR_POSITIVO = "#2a78d6"` nem em `COR_NEGATIVO = "#e34948"`**:
são cores de dado, validadas para contraste e fora de escopo. Nenhuma outra
linha do arquivo muda.

**4. Substituir `frontend/src/index.css` inteiro pelo conteúdo abaixo.**

```css
/* Vocabulário visual único do app: paleta de 6 tokens, tipografia e o sistema de
   pautas — fio de cabelo entre linhas, fio simples sobre subtotal, fio duplo sob
   o total final. O dispositivo estrutural é o fio, não a caixa: nenhuma tabela é
   envolvida em cartão.

   Tipografia segue na pilha de sistema nesta rodada; uma serifada
   auto-hospedada para o corpo do relatório foi considerada e deliberadamente
   adiada. Não re-adicionar.

   Tema claro apenas — nenhuma regra prefers-color-scheme, de propósito. */

:root {
  --papel: #fcfcfb;
  --tinta: #1a2233;
  --tinta-fraca: #5a6472;
  --pauta: #c8cdd6;
  --pauta-fraca: #e3e6eb;
  --vermelho: #a4243b;
}

body {
  font-family: system-ui, sans-serif;
  margin: 0;
  background: var(--papel);
  color: var(--tinta);
}

/* ---- navegação ----
   Papel, não laje: a aba ativa é marcada por um fio de tinta embaixo, e por mais
   nada. Sem fundo, sem caixa, sem canto arredondado — o mesmo dispositivo das
   tabelas. */

.tabs {
  display: flex;
  gap: 4px;
  background: var(--papel);
  border-bottom: 1px solid var(--pauta);
  padding: 8px 24px 0;
}

.tab {
  background: transparent;
  color: var(--tinta-fraca);
  font: inherit;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding: 8px 12px;
  cursor: pointer;
}

.tab-ativa {
  color: var(--tinta);
  border-bottom-color: var(--tinta);
  font-weight: 600;
}

main {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 16px;
}

h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 4px;
}

h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--tinta-fraca);
  margin: 16px 0 4px;
}

/* ---- o sistema de pautas ----
   Toda tabela do app é um razão; por isso o estilo é por elemento e nenhuma
   página precisa de classe na tag <table>. Larguras de borda escolhidas para
   resolver a colapsagem sem ambiguidade: na colapsagem a borda mais larga
   vence, então 2px (subtotal) > 1px (fio de cabelo) e 3px double (total) >
   2px. */

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

th,
td {
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid var(--pauta);
}

thead th {
  font-size: 13px;
  font-weight: 600;
  color: var(--tinta-fraca);
  border-bottom: 1px solid var(--tinta);
}

/* Dinheiro: à direita, algarismos tabulares para as colunas alinharem
   verticalmente entre linhas. Vale para <th> e <td>. */
.razao-valor {
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.valor-negativo {
  color: var(--vermelho);
}

/* Fio simples acima: é um subtotal. */
.razao-subtotal > td {
  font-weight: 600;
  border-top: 2px solid var(--tinta);
}

/* Total final fora de tabela: fio simples acima, fio duplo abaixo. */
.razao-fechamento {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin: 16px 0 0;
  padding: 6px 10px;
  font-weight: 700;
  border-top: 2px solid var(--tinta);
  border-bottom: 3px double var(--tinta);
}

.tabela-rolagem {
  overflow-x: auto;
}

/* TEMPORÁRIO — ainda usada por BalancoPatrimonial.jsx e DRE.jsx até as Tarefas 4
   e 5. Removida na Tarefa 6. */
.total-linha {
  font-weight: bold;
  border-top: 2px solid var(--tinta);
}

/* ---- formulário ---- */

.form-lancamento {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px 20px;
  align-items: end;
  margin-top: 16px;
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.campo-rotulo {
  font-size: 12px;
  font-weight: 600;
  color: var(--tinta-fraca);
}

.campo input,
.campo select {
  font: inherit;
  color: var(--tinta);
  background: var(--papel);
  border: 1px solid var(--pauta);
  border-radius: 2px;
  padding: 6px 8px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.campo input[type="number"] {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.campo input:focus,
.campo select:focus {
  outline: 2px solid var(--tinta);
  outline-offset: 1px;
}

input[type="file"] {
  font: inherit;
  color: var(--tinta-fraca);
}

.botao {
  font: inherit;
  color: var(--tinta);
  background: var(--papel);
  border: 1px solid var(--tinta);
  border-radius: 2px;
  padding: 7px 18px;
  cursor: pointer;
}

.botao:hover {
  color: var(--papel);
  background: var(--tinta);
}

.form-lancamento .botao {
  justify-self: start;
}

/* ---- conta T do Balanço Patrimonial ----
   A ousadia é gasta em um lugar só: este fio vertical. */

.bp-colunas {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin-top: 16px;
}

.bp-coluna {
  min-width: 0;
}

.bp-coluna:first-child {
  padding-right: 28px;
}

.bp-coluna:last-child {
  padding-left: 28px;
  border-left: 2px solid var(--tinta);
}

/* ---- recusas ---- */

.erro {
  color: var(--vermelho);
}

/* Âmbar validado para contraste (≈6,8:1 sobre --papel); fora de escopo desta
   revisão, fica literal de propósito. */
.grafico-aviso,
.analise-nao-significativo {
  color: #92400e;
}

/* ---- gráficos ---- */

/* Sem cartão: um fio acima, como divisor de seção, na mesma pauta das tabelas.
   O fundo sai porque o body já é --papel, que é a cor de que o SUPERFICIE do
   GraficoBalanco depende para pintar os vãos entre segmentos.
   REVERSÍVEL: para devolver a caixa, troque as três primeiras declarações
   (`border-top`, `padding`, `margin-top`) por `background: var(--papel);
   border: 1px solid var(--pauta); border-radius: 6px; padding: 16px;
   margin-top: 12px;`, mantendo o `overflow-x: auto`. */
.grafico {
  border-top: 1px solid var(--pauta);
  padding: 16px 0 0;
  margin-top: 24px;
  overflow-x: auto;
}

.grafico h3 {
  margin: 0;
  font-size: 15px;
  color: var(--tinta);
}

.grafico-subtitulo {
  margin: 4px 0 12px;
  font-size: 12px;
  color: var(--tinta-fraca);
}

.grafico svg {
  display: block;
  width: 100%;
  height: auto;
  margin: 0 auto;
}

.grafico-bp svg {
  max-width: 420px;
  min-width: 420px;
}

.grafico-dre svg {
  max-width: 720px;
  min-width: 720px;
}

.grafico-legenda {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  margin: 12px 0 0;
  padding: 0;
  font-size: 12px;
  color: var(--tinta-fraca);
  font-variant-numeric: tabular-nums;
}

.grafico-legenda li {
  display: flex;
  align-items: center;
  gap: 6px;
}

.grafico-legenda-cor {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex: none;
}

.grafico-vazio {
  margin: 0;
  padding: 24px 0;
  text-align: center;
  font-size: 13px;
  color: var(--tinta-fraca);
}

/* ---- Análise ---- */

.analise-intro {
  font-size: 13px;
  color: var(--tinta-fraca);
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
  color: var(--tinta-fraca);
  margin-top: 2px;
}

/* Sem face monoespaçada: algarismos tabulares na face proporcional alinham os
   números sem o tell do monoespaçado em rótulo pequeno de dado. */
.analise-substituicao {
  font-size: 12px;
  color: var(--tinta-fraca);
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}

.analise-direcao {
  font-size: 12px;
  color: var(--tinta-fraca);
  margin-top: 2px;
}

.analise-observacao {
  font-size: 12px;
  color: var(--tinta-fraca);
  margin-top: 4px;
  max-width: 52ch;
}

.analise-valor {
  text-align: right;
  white-space: nowrap;
  font-size: 18px;
  width: 40%;
  font-variant-numeric: tabular-nums;
}

.analise-motivo {
  font-size: 12px;
  font-weight: normal;
  color: var(--tinta-fraca);
  text-align: right;
  white-space: normal;
  margin-top: 4px;
}

/* ---- telas estreitas ---- */

@media (max-width: 720px) {
  main {
    padding: 16px;
  }

  .tabs {
    padding: 8px 16px 0;
    overflow-x: auto;
  }

  .form-lancamento {
    grid-template-columns: 1fr;
  }

  .bp-colunas {
    grid-template-columns: 1fr;
  }

  .bp-coluna:first-child {
    padding-right: 0;
  }

  .bp-coluna:last-child {
    padding-left: 0;
    padding-top: 24px;
    margin-top: 24px;
    border-left: none;
    border-top: 2px solid var(--tinta);
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

**5. Rodar o build.**

```
cd frontend && npm run build
```

Espere: `vite build` terminando com `✓ built in <tempo>` e código de saída 0.
Nenhum aviso novo de import não resolvido.

**6. Verificar que nenhuma cor antiga sobrou nos arquivos desta tarefa.**

```
cd frontend && grep -n "#0b0b0b\|#f5f5f5\|#52514e\|#898781\|#c3c2b7\|#e1e0d9\|#ddd\|#b91c1c" src/index.css src/components/graficos-comuns.js src/components/GraficoDRE.jsx index.html
```

Espere: **nenhuma linha de saída** (código de saída 1 do grep, que é o
esperado).

**7. Commitar.**

```
git add frontend/index.html frontend/src/index.css frontend/src/components/graficos-comuns.js frontend/src/components/GraficoDRE.jsx
git commit -m "Define paleta de 6 tokens, sistema de pautas e meta viewport"
```

---

# Tarefa 2 — Lançamentos: formulário em grade e valor formatado

### Arquivos

- `frontend/src/pages/Lancamentos.jsx` — **Modificar**

### Interfaces

**Consome** (definidos na Tarefa 1, já no repositório):

- De `../components/graficos-comuns`: `fmt(valor)` → string pt-BR com 2 casas e
  separador de milhar (`50000` → `"50.000,00"`); `classeValor(valor)` → `string`
  com o(s) nome(s) de classe da célula de dinheiro.
- Classes CSS: `.form-lancamento`, `.campo`, `.campo-rotulo`, `.botao`,
  `.razao-valor`, `.tabela-rolagem`, `.erro`.

**Produz:** nada que outras tarefas consumam.

### Passos

**1. Acrescentar o import do vocabulário compartilhado.**

Abaixo da linha de import de `../api`, acrescente:

```jsx
import { fmt, classeValor } from "../components/graficos-comuns";
```

**2. Substituir o `<form>` inteiro pela grade com rótulo acima do campo.**

Troque o bloco `<form onSubmit={aoSubmeter}> … </form>` por:

```jsx
      <form className="form-lancamento" onSubmit={aoSubmeter}>
        <label className="campo">
          <span className="campo-rotulo">Data</span>
          <input
            type="date"
            value={form.data}
            onChange={(e) => setForm({ ...form, data: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Conta débito</span>
          <select
            value={form.conta_debito}
            onChange={(e) => setForm({ ...form, conta_debito: e.target.value })}
            required
          >
            <option value="">Selecione</option>
            {contas.map((conta) => (
              <option key={conta.codigo} value={conta.codigo}>
                {conta.codigo} - {conta.nome}
              </option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span className="campo-rotulo">Conta crédito</span>
          <select
            value={form.conta_credito}
            onChange={(e) => setForm({ ...form, conta_credito: e.target.value })}
            required
          >
            <option value="">Selecione</option>
            {contas.map((conta) => (
              <option key={conta.codigo} value={conta.codigo}>
                {conta.codigo} - {conta.nome}
              </option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span className="campo-rotulo">Valor</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={form.valor}
            onChange={(e) => setForm({ ...form, valor: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Histórico</span>
          <input
            type="text"
            value={form.historico}
            onChange={(e) => setForm({ ...form, historico: e.target.value })}
          />
        </label>
        <button type="submit" className="botao">
          Lançar
        </button>
      </form>
```

Nada de comportamento muda: mesmos `value`, mesmos `onChange`, mesmos `required`,
mesmo `type`/`step`/`min`, mesma ordem de campos, mesmo `onSubmit`. O rótulo
textual sai de filho direto do `<label>` para dentro de um `<span>` — o
`<label>` continua envolvendo o campo, então a associação rótulo↔campo continua
implícita e nenhum `id`/`htmlFor` é necessário.

**3. Envolver a tabela de lançamentos existentes e formatar o valor.**

Troque o bloco que começa em `<h3>Lançamentos existentes</h3>` e vai até o
`</table>` por:

```jsx
      <h3>Lançamentos existentes</h3>
      <div className="tabela-rolagem">
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Débito</th>
              <th>Crédito</th>
              <th className="razao-valor">Valor</th>
              <th>Histórico</th>
            </tr>
          </thead>
          <tbody>
            {lancamentos.map((lancamento) => (
              <tr key={lancamento.id}>
                <td>{lancamento.data}</td>
                <td>{lancamento.conta_debito}</td>
                <td>{lancamento.conta_credito}</td>
                <td className={classeValor(lancamento.valor)}>
                  {fmt(lancamento.valor)}
                </td>
                <td>{lancamento.historico}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
```

O `<th>Valor</th>` recebe `.razao-valor` para o cabeçalho alinhar com a coluna
de números.

**4. Conferir que não sobrou `toFixed` no arquivo.**

```
cd frontend && grep -n "toFixed" src/pages/Lancamentos.jsx
```

Espere: **nenhuma linha de saída**.

**5. Rodar o build.**

```
cd frontend && npm run build
```

Espere: `✓ built in <tempo>`, saída 0.

**6. Commitar.**

```
git add frontend/src/pages/Lancamentos.jsx
git commit -m "Lançamentos: formulário em grade e valor no formato pt-BR"
```

---

# Tarefa 3 — Balancete: colunas de dinheiro à direita e formatadas

### Arquivos

- `frontend/src/pages/Balancete.jsx` — **Modificar**

### Interfaces

**Consome** (já no repositório):

- De `../components/graficos-comuns`: `fmt(valor)` → string pt-BR
  (`38000` → `"38.000,00"`); `classeValor(valor)` → `"razao-valor"` ou
  `"razao-valor valor-negativo"`.
- Classes CSS: `.razao-valor`, `.tabela-rolagem`, `.erro`. O fio de cabelo entre
  linhas e o fio sob o cabeçalho já vêm do estilo global de `table`/`th, td`/
  `thead th` — **não** adicione classe na tag `<table>`.

**Produz:** nada que outras tarefas consumam.

**Nota de escopo:** o balancete **não ganha linha de Subtotal**. O desenho da
convenção mostra uma para ilustrar a pauta, mas essa linha não existe nos dados
que a página recebe e somá-la aqui seria um cálculo novo no frontend — proibido
pelas restrições globais.

### Passos

**1. Acrescentar o import.**

Abaixo do import de `../api`:

```jsx
import { fmt, classeValor } from "../components/graficos-comuns";
```

**2. Substituir o bloco `<table> … </table>` por:**

```jsx
      <div className="tabela-rolagem">
        <table>
          <thead>
            <tr>
              <th>Conta</th>
              <th>Grupo</th>
              <th className="razao-valor">Total débito</th>
              <th className="razao-valor">Total crédito</th>
              <th className="razao-valor">Saldo</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((linha) => (
              <tr key={linha.codigo}>
                <td>
                  {linha.codigo} - {linha.nome}
                </td>
                <td>{linha.grupo}</td>
                <td className={classeValor(linha.total_debito)}>
                  {fmt(linha.total_debito)}
                </td>
                <td className={classeValor(linha.total_credito)}>
                  {fmt(linha.total_credito)}
                </td>
                <td className={classeValor(linha.saldo)}>{fmt(linha.saldo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
```

Nenhum outro trecho do arquivo muda: `useState`, `useEffect`, `getBalancete`, o
`<h2>` e o parágrafo `.erro` ficam como estão.

**3. Conferir que não sobrou `toFixed`.**

```
cd frontend && grep -n "toFixed" src/pages/Balancete.jsx
```

Espere: **nenhuma linha de saída**.

**4. Rodar o build.**

```
cd frontend && npm run build
```

Espere: `✓ built in <tempo>`, saída 0.

**5. Commitar.**

```
git add frontend/src/pages/Balancete.jsx
git commit -m "Balancete: dinheiro à direita, tabular e no formato pt-BR"
```

---

# Tarefa 4 — Balanço Patrimonial: a conta T

Esta é a tarefa onde a ousadia é gasta: o fio vertical entre Ativo e Passivo+PL
expressa a dualidade débito/crédito estruturalmente, sem rótulo.

### Arquivos

- `frontend/src/pages/BalancoPatrimonial.jsx` — **Modificar**

### Interfaces

**Consome** (já no repositório):

- De `../components/graficos-comuns`: `fmt(valor)` → string pt-BR
  (`79760` → `"79.760,00"`); `classeValor(valor)` → `"razao-valor"` ou
  `"razao-valor valor-negativo"`.
- Classes CSS: `.bp-colunas` (grade de duas colunas), `.bp-coluna` (cada lado; a
  **segunda** recebe o fio vertical automaticamente via `:last-child`, não há
  classe modificadora a aplicar), `.razao-subtotal` (`<tr>` de subtotal),
  `.razao-fechamento` (linha de total final, com dois `<span>` filhos),
  `.razao-valor`, `.erro`.
- De `../components/GraficoBalanco`: componente default `GraficoBalanco`, prop
  `bp`. Não muda.

**Produz:** nada que outras tarefas consumam.

**Some daqui:** a classe `.total-linha` e o `style={{ display: "flex", gap:
"32px" }}` inline.

### Passos

**1. Acrescentar o import de `fmt` e `classeValor`.**

O topo do arquivo passa a ser:

```jsx
import { useEffect, useState } from "react";
import { getBP } from "../api";
import GraficoBalanco from "../components/GraficoBalanco";
import { fmt, classeValor } from "../components/graficos-comuns";
```

**2. Substituir o componente `Coluna` inteiro por:**

```jsx
function Coluna({ titulo, secoes, total }) {
  return (
    <div className="bp-coluna">
      <h3>{titulo}</h3>
      {secoes.map((secao) => (
        <div key={secao.grupo}>
          <h4>{secao.grupo}</h4>
          <table>
            <tbody>
              {secao.contas.map((conta) => (
                <tr key={conta.codigo}>
                  <td>{conta.nome}</td>
                  <td className={classeValor(conta.saldo)}>
                    {fmt(conta.saldo)}
                  </td>
                </tr>
              ))}
              <tr className="razao-subtotal">
                <td>Subtotal</td>
                <td className={classeValor(secao.subtotal)}>
                  {fmt(secao.subtotal)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}
      <p className="razao-fechamento">
        <span>Total</span>
        <span className={classeValor(total)}>{fmt(total)}</span>
      </p>
    </div>
  );
}
```

O rótulo do fechamento passa de `Total: 79.760,00` para `Total` à esquerda e
`79.760,00` à direita — mesma informação, separada pelo `space-between` de
`.razao-fechamento`. O dois-pontos sai porque o fio duplo e o alinhamento já
fazem o trabalho dele.

**3. Substituir o `return` do componente `BalancoPatrimonial` por:**

```jsx
  return (
    <section>
      <h2>Balanço Patrimonial</h2>
      {!bp.balanceado && (
        <p className="erro">
          Atenção: Ativo ({fmt(bp.total_ativo)}) não bate com Passivo + PL (
          {fmt(bp.total_passivo_pl)}).
        </p>
      )}
      <GraficoBalanco bp={bp} />
      <div className="bp-colunas">
        <Coluna titulo="Ativo" secoes={bp.ativo} total={bp.total_ativo} />
        <Coluna
          titulo="Passivo + Patrimônio Líquido"
          secoes={bp.passivo_pl}
          total={bp.total_passivo_pl}
        />
      </div>
    </section>
  );
```

A ordem das duas `<Coluna>` importa: Ativo primeiro (sem fio), Passivo + PL
segundo (recebe o fio vertical à esquerda via `.bp-coluna:last-child`).

Os dois `early return` acima (`if (erro)` e `if (!bp)`) ficam exatamente como
estão.

**4. Conferir que não sobrou `toFixed` nem `total-linha`.**

```
cd frontend && grep -n "toFixed\|total-linha" src/pages/BalancoPatrimonial.jsx
```

Espere: **nenhuma linha de saída**.

**5. Rodar o build.**

```
cd frontend && npm run build
```

Espere: `✓ built in <tempo>`, saída 0.

**6. Commitar.**

```
git add frontend/src/pages/BalancoPatrimonial.jsx
git commit -m "Balanço Patrimonial: conta T com fio vertical e pautas de subtotal"
```

---

# Tarefa 5 — DRE: subtotais com fio simples, resultado com fio duplo

### Arquivos

- `frontend/src/pages/DRE.jsx` — **Modificar**

### Interfaces

**Consome** (já no repositório):

- De `../components/graficos-comuns`: `fmt(valor)` → string pt-BR
  (`-1500` → `"-1.500,00"`, com hífen — é o sinal que o `Intl` pt-BR emite e é
  o que o app usa); `classeValor(valor)` → `"razao-valor"` ou
  `"razao-valor valor-negativo"`.
- Classes CSS: `.razao-subtotal`, `.razao-fechamento`, `.razao-valor`, `.erro`.
- De `../components/GraficoDRE`: componente default `GraficoDRE`, prop `dre`.
  Não muda.

**Produz:** nada que outras tarefas consumam.

**Hierarquia da pauta nesta página** (é o que decide qual classe vai onde):
"Total de receitas" e "Total de despesas" são **subtotais** — alimentam o
resultado — e portanto levam fio simples acima (`.razao-subtotal`). O
"Resultado do período" é o **total final** da demonstração e leva fio simples
acima + fio duplo abaixo (`.razao-fechamento`). Não inverta.

### Passos

**1. Acrescentar o import.**

O topo do arquivo passa a ser:

```jsx
import { useEffect, useState } from "react";
import { getDRE } from "../api";
import GraficoDRE from "../components/GraficoDRE";
import { fmt, classeValor } from "../components/graficos-comuns";
```

**2. Substituir tudo do `<h3>Receitas</h3>` até o fim do `return` por:**

```jsx
      <h3>Receitas</h3>
      <table>
        <tbody>
          {dre.receitas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td className={classeValor(conta.valor)}>{fmt(conta.valor)}</td>
            </tr>
          ))}
          <tr className="razao-subtotal">
            <td>Total de receitas</td>
            <td className={classeValor(dre.total_receitas)}>
              {fmt(dre.total_receitas)}
            </td>
          </tr>
        </tbody>
      </table>

      <h3>Despesas</h3>
      <table>
        <tbody>
          {dre.despesas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td className={classeValor(conta.valor)}>{fmt(conta.valor)}</td>
            </tr>
          ))}
          <tr className="razao-subtotal">
            <td>Total de despesas</td>
            <td className={classeValor(dre.total_despesas)}>
              {fmt(dre.total_despesas)}
            </td>
          </tr>
        </tbody>
      </table>

      <p className="razao-fechamento">
        <span>
          Resultado do período
          {dre.resultado_periodo >= 0 ? " (lucro)" : " (prejuízo)"}
        </span>
        <span className={classeValor(dre.resultado_periodo)}>
          {fmt(dre.resultado_periodo)}
        </span>
      </p>
    </section>
  );
}
```

A informação é a mesma de antes — rótulo, marcação lucro/prejuízo e valor — só
reordenada: o `(lucro)`/`(prejuízo)` gruda no rótulo à esquerda e o número vai
para a direita, com o `>= 0` idêntico ao original. Um CMV negativo em
`dre.despesas` (caso que a fixture de casos extremos produz) agora aparece em
vermelho via `classeValor`, e o parágrafo `.grafico-aviso` do `GraficoDRE`
continua explicando por que a cascata não o representa.

Nada acima do `<h3>Receitas</h3>` muda: `useState`, `useEffect`, os dois
`early return` e o `<GraficoDRE dre={dre} />` ficam como estão.

**3. Conferir que não sobrou `toFixed` nem `total-linha`.**

```
cd frontend && grep -n "toFixed\|total-linha" src/pages/DRE.jsx
```

Espere: **nenhuma linha de saída**.

**4. Rodar o build.**

```
cd frontend && npm run build
```

Espere: `✓ built in <tempo>`, saída 0.

**5. Commitar.**

```
git add frontend/src/pages/DRE.jsx
git commit -m "DRE: subtotais com fio simples e resultado com fio duplo"
```

---

# Tarefa 6 — Remover a classe de transição e varrer o frontend

A página de Análise **não precisa de mudança de código**: ela já usa `fmt` em
todos os números, e a remoção do monoespaçado, os algarismos tabulares e a
retokenização de cor já vieram pelo CSS da Tarefa 1. Esta tarefa fecha o plano
removendo a classe que existia só para as tarefas intermediárias não deixarem a
tela quebrada, e provando por varredura que o app inteiro fala uma língua só.

### Arquivos

- `frontend/src/index.css` — **Modificar** (remover um bloco de 4 linhas + o
  comentário)

### Interfaces

**Consome:** o resultado das Tarefas 1–5. Em particular, que nenhum `.jsx` de
`frontend/src/` referencia mais `total-linha` (as Tarefas 4 e 5 removeram as
cinco referências) e que nenhum referencia `toFixed` (as Tarefas 2–5 removeram
as catorze).

**Produz:** nada.

### Passos

**1. Confirmar que `.total-linha` está órfã antes de removê-la.**

```
cd frontend && grep -rn "total-linha" src
```

Espere **exatamente uma linha de saída**, a definição no CSS:

```
src/index.css:<n>:.total-linha {
```

Se aparecer qualquer ocorrência em `src/pages/` ou `src/components/`, **pare**:
alguma tarefa anterior ficou incompleta e este passo não deve prosseguir.

**2. Remover o bloco de transição de `frontend/src/index.css`.**

Apague estas seis linhas (o comentário e a regra), inclusive a linha em branco
que as separa da regra seguinte:

```css
/* TEMPORÁRIO — ainda usada por BalancoPatrimonial.jsx e DRE.jsx até as Tarefas 4
   e 5. Removida na Tarefa 6. */
.total-linha {
  font-weight: bold;
  border-top: 2px solid var(--tinta);
}
```

Nenhuma outra regra do arquivo muda.

**3. Varredura: nenhum `.toFixed` em lugar nenhum do frontend.**

```
cd frontend && grep -rn "toFixed" src
```

Espere: **nenhuma linha de saída**.

**4. Varredura: nenhuma cor da paleta antiga sobrando.**

```
cd frontend && grep -rn "#0b0b0b\|#f5f5f5\|#52514e\|#898781\|#c3c2b7\|#e1e0d9\|#b91c1c\|#1f2937\|#374151\|#ddd\|#333" src index.html
```

Espere: **nenhuma linha de saída**.

**5. Varredura: nenhuma regra de tema escuro e nenhuma fonte externa.**

```
cd frontend && grep -rn "prefers-color-scheme\|fonts.googleapis\|@font-face\|@import" src index.html
```

Espere: **nenhuma linha de saída**.

**6. Varredura: nenhuma face monoespaçada sobrando.**

```
cd frontend && grep -rn "monospace\|ui-monospace" src
```

Espere: **nenhuma linha de saída**.

**7. Confirmar que `package.json` não mudou no branch.**

```
git diff master --stat -- frontend/package.json frontend/package-lock.json
```

Espere: **nenhuma linha de saída** (nenhum dos dois arquivos foi tocado).

**8. Confirmar que o backend não foi tocado no branch.**

```
git diff master --stat -- backend
```

Espere: **nenhuma linha de saída**.

**9. Rodar o build.**

```
cd frontend && npm run build
```

Espere: `✓ built in <tempo>`, saída 0.

**10. Commitar.**

```
git add frontend/src/index.css
git commit -m "Remove .total-linha, substituída pelas pautas de subtotal e fechamento"
```

---

## Verificação final (coordenador, no navegador)

Fora do escopo das tarefas — nenhum implementador executa esta seção. Depois da
Tarefa 6, com o backend rodando e `npm run dev` no frontend:

1. **Lançamentos** — formulário em três colunas, rótulo acima do campo, botão
   "Lançar" na coluna 3 da segunda linha; coluna Valor à direita com separador
   de milhar.
2. **Balancete** — as três colunas de dinheiro à direita, algarismos alinhados
   verticalmente entre linhas, fio sob o cabeçalho, fio de cabelo entre linhas.
3. **Balanço Patrimonial** — fio vertical entre as duas colunas; fio simples
   acima de cada Subtotal; fio duplo sob cada Total; se houver PL negativo, o
   número em vermelho e o `aviso` âmbar do gráfico intacto.
4. **DRE** — fio simples acima dos dois totais; fio duplo sob o Resultado do
   período; prejuízo em vermelho.
5. **Análise** — linha de substituição sem monoespaçado, números alinhados; o
   âmbar de `não-significativo` e os textos de `observacao`/`motivo` intactos.
5a. **Barra de abas** — papel, não laje; a aba ativa marcada só pelo fio de
   tinta embaixo, sem fundo nem canto arredondado.
5b. **Gráficos sem cartão** — é o ponto que o coordenador quer julgar: com o fio
   acima no lugar do contorno, o gráfico ancora ou fica solto? Se ficar solto, a
   caixa volta trocando as três primeiras declarações de `.grafico` (o bloco tem
   a instrução em comentário). Conferir junto que os vãos entre segmentos
   empilhados do gráfico de BP continuam invisíveis — se aparecerem faixas
   claras, o `SUPERFICIE` deixou de bater com o fundo.
5c. **Conector da cascata da DRE** — o fio horizontal entre os passos deve
   continuar visível e continuar mais leve que a linha do zero. Se sumiu,
   escureça `--pauta-fraca`; não mexa em mais nada.
6. **Largura estreita** (DevTools ~390px) — formulário em uma coluna; conta T
   empilhada com fio horizontal separando os lados; tabelas largas rolando
   dentro de `.tabela-rolagem` sem estourar a página.
7. **Uma superfície só** — nenhuma faixa de cinza diferente entre o corpo da
   página e os cartões de gráfico.

## Questões levantadas no planejamento e como foram fechadas

As quatro questões que o design não cobria foram decididas pelo coordenador e já
estão **implementadas nas tarefas acima**. Ficam registradas para quem ler o
plano depois não reabrir nenhuma delas.

1. **A barra de abas — convertida.** O design não fala dela, mas ela usava
   `#1f2937`/`#374151`, fora da paleta, e laje escura é o cromo aplicado que
   este trabalho remove. Vira papel; a aba ativa é marcada **só** pelo fio de
   tinta embaixo — sem caixa, sem fundo, sem canto arredondado. Tarefa 1.
2. **O cartão dos gráficos — removido.** Com corpo e cartão na mesma superfície,
   o contorno perde função, e manter um elemento em caixa enquanto todo o resto
   é pautado é a incoerência que o trabalho existe para eliminar. No lugar,
   um fio acima do bloco, como divisor de seção. O SVG não muda. **Reversível em
   uma regra de CSS**, e é o ponto que o coordenador mais quer julgar no
   navegador: se o gráfico ficar solto, o contorno volta. Tarefa 1.
3. **Subtotal no Balancete — não entra, e isso é dívida, não desleixo.** A
   restrição de "nenhum cálculo novo no frontend" é explícita e o plano a
   respeita. Mas vale dizer o que fica faltando: o balancete existe justamente
   para mostrar que Σdébitos = Σcréditos, e hoje o app não exibe a única soma
   que prova a partida dobrada diretamente. O caminho certo é o **backend
   devolver os totais no endpoint do balancete**, e a página só formatá-los com
   `fmt` numa linha `.razao-subtotal` — que já existe no vocabulário desde a
   Tarefa 1. Trabalho separado, outro plano, com teste pytest próprio.
4. **`COR_CONECTOR` — aponta para `--pauta-fraca` (`#e3e6eb`).** Nem manter
   `#e1e0d9` (cinza quente numa paleta que virou fria-neutra) nem igualar a
   `--pauta` (perderia a subordinação deliberada do conector ao eixo). O sexto
   token resolve as duas coisas de uma vez. Tarefa 1, passo 3.
