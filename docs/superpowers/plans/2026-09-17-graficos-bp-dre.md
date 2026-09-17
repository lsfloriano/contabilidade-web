# Gráficos do Balanço Patrimonial e da DRE

Plano de implementação — branch `feat/graficos`.

## Objetivo

Adicionar duas visualizações ao frontend, **acima** das tabelas existentes, sem
tocar no backend e sem adicionar dependências npm:

1. **Balanço Patrimonial** — barras empilhadas comparativas (Ativo x Passivo + PL)
   em escala Y compartilhada. Quando o balanço fecha, as duas barras têm
   exatamente a mesma altura: essa identidade visual é o ponto pedagógico do
   gráfico.
2. **DRE** — cascata (waterfall): Receitas sobe do zero, cada despesa com
   `valor > 0` desce em sequência, e uma barra final de Resultado colorida pelo
   sinal.

As tabelas permanecem **exatamente como estão** — continuam sendo os números
autoritativos; o gráfico é a leitura de relance.

## Restrições globais (valem para todas as tarefas)

- **Somente frontend.** Nenhuma alteração em `backend/`. A suíte de 20 testes do
  backend (`cd backend && pytest -v`) não é tocada por este trabalho.
- **Zero dependências novas.** `frontend/package.json` não muda. Nada de Recharts,
  D3, Chart.js. Os dois gráficos são SVG inline escrito à mão.
- **Sem testes automatizados de frontend.** Decisão de escopo deliberada e
  documentada do projeto. Não adicione Vitest/Jest/Testing Library e não escreva
  tarefas de teste de frontend. O **portão automatizado de cada tarefa é
  `npm run build` passando a partir de `frontend/`**. A verificação manual no
  navegador é feita depois, pelo coordenador — não pelo implementador.
- **Idioma:** todas as strings visíveis ao usuário em português (pt-BR),
  acompanhando as páginas existentes.
- **Estilo de código existente:** componentes de função, hooks, sem framework de
  CSS, `className` em strings simples, `style` inline apenas onde o código
  existente já usa.
- O app é **somente tema claro** (`frontend/src/index.css` não tem nenhuma regra
  `prefers-color-scheme`). Por isso apenas os passos de cor do modo claro são
  usados, validados contra a superfície de gráfico `#fcfcfb`. Não adicione
  variáveis nem blocos de tema escuro.

## Paleta (já validada — não re-derive)

Os valores abaixo saíram da skill `dataviz` e foram validados com
`scripts/validate_palette.js` contra a superfície `#fcfcfb` no modo claro.
**Transcreva os hex literalmente; não invente nem substitua cores.**

Categórica (ordem fixa dos slots 1–5), usada nos 5 grupos do BP:

| Ordem | Grupo | Hex |
|---|---|---|
| 1 | Ativo Circulante | `#2a78d6` |
| 2 | Ativo Não Circulante | `#eb6834` |
| 3 | Passivo Circulante | `#1baf7a` |
| 4 | Passivo Não Circulante | `#eda100` |
| 5 | Patrimônio Líquido | `#e87ba4` |

Resultado da validação (pairlist adjacente — o pairlist correto para barra
empilhada): lightness band PASS, chroma floor PASS, separação CVD PASS
(pior par ΔE 9.1), piso de visão normal PASS (pior par ΔE 19.6), contraste WARN
para `#1baf7a`, `#eda100` e `#e87ba4` (abaixo de 3:1 na superfície). O WARN de
contraste **obriga relevo**, que aqui é atendido de duas formas simultâneas: a
legenda imprime o valor de cada grupo em texto, e as tabelas da própria página
logo abaixo são a "table view" com todos os números.

Divergente (par quente/frio), usada na DRE:

| Papel | Hex |
|---|---|
| Aumenta o resultado (receitas, lucro) | `#2a78d6` |
| Reduz o resultado (despesas, prejuízo) | `#e34948` |

Validação com `--pairs all`: todos os seis checks PASS (CVD ΔE 21.6, visão
normal ΔE 32.3, contraste ≥ 3:1).

Cromo e tinta (iguais nos dois gráficos):

| Papel | Hex |
|---|---|
| Superfície do gráfico | `#fcfcfb` |
| Tinta primária (valores em destaque) | `#0b0b0b` |
| Tinta secundária (rótulos de eixo) | `#52514e` |
| Tinta apagada (tick do zero, estado vazio) | `#898781` |
| Hairline / conector | `#e1e0d9` |
| Linha de base / eixo | `#c3c2b7` |
| Borda do cartão | `rgba(11, 11, 11, 0.1)` |

## Especificações de marca (da skill `dataviz`)

- Barra com **24px de espessura**, nunca preenchendo a faixa — a sobra da faixa é ar.
- **4px de arredondamento na ponta de dados**, quadrado na base.
- **Vão de 2px na cor da superfície** separando segmentos empilhados. Nunca uma
  borda desenhada em volta da marca.
- Linhas de eixo e conectores: hairline de 1px, **sólidas** (nunca tracejadas),
  recessivas.
- **Legenda sempre presente** quando há 2+ séries; rótulos diretos são seletivos.
- **Texto nunca veste a cor da série** — rótulos e legendas usam tinta primária /
  secundária / apagada; a identidade vem do quadradinho colorido ao lado.
- Camada de hover: `<title>` dentro de cada marca SVG (tooltip nativo do
  navegador, custo zero de dependência). O tooltip **complementa**, nunca é a
  única via de leitura — todos os valores também estão na legenda e nas tabelas.

## Formas de arquivo

| Arquivo | Ação |
|---|---|
| `frontend/src/index.css` | Modificar (Tarefa 1) |
| `frontend/src/components/GraficoBalanco.jsx` | Criar (Tarefa 2) |
| `frontend/src/pages/BalancoPatrimonial.jsx` | Modificar (Tarefa 2) |
| `frontend/src/components/GraficoDRE.jsx` | Criar (Tarefa 3) |
| `frontend/src/pages/DRE.jsx` | Modificar (Tarefa 3) |

A Tarefa 1 precede as outras duas (elas consomem as classes de CSS). As Tarefas 2
e 3 são independentes entre si.

---

## Tarefa 1 — Classes de CSS dos gráficos

### Files

- `frontend/src/index.css` — **Modify**

### Interfaces

**Consome:** nada.

**Produz** — as classes de CSS que os componentes de gráfico das tarefas
seguintes usam pelo nome exato:

- `.grafico` — cartão do gráfico (superfície, borda, padding).
- `.grafico-bp` — modificador do cartão do Balanço Patrimonial; limita o SVG a
  420px de largura.
- `.grafico-dre` — modificador do cartão da DRE; limita o SVG a 720px de largura.
- `.grafico-subtitulo` — parágrafo de legenda explicativa sob o `<h3>` do cartão.
- `.grafico-legenda` — `<ul>` horizontal da legenda.
- `.grafico-legenda-cor` — `<span>` quadradinho de 10px que recebe
  `style={{ background: <hex> }}`.
- `.grafico-vazio` — `<p>` do estado vazio.

### Steps

1. Abra `frontend/src/index.css`. **Não altere nenhuma regra existente.** Acrescente
   os blocos abaixo ao **final** do arquivo, exatamente como escritos:

   ```css

   .grafico {
     background: #fcfcfb;
     border: 1px solid rgba(11, 11, 11, 0.1);
     border-radius: 6px;
     padding: 16px;
     margin-top: 12px;
   }

   .grafico h3 {
     margin: 0;
     font-size: 15px;
     color: #0b0b0b;
   }

   .grafico-subtitulo {
     margin: 4px 0 12px;
     font-size: 12px;
     color: #52514e;
   }

   .grafico svg {
     display: block;
     width: 100%;
     height: auto;
     margin: 0 auto;
   }

   .grafico-bp svg {
     max-width: 420px;
   }

   .grafico-dre svg {
     max-width: 720px;
   }

   .grafico-legenda {
     list-style: none;
     display: flex;
     flex-wrap: wrap;
     gap: 8px 20px;
     margin: 12px 0 0;
     padding: 0;
     font-size: 12px;
     color: #52514e;
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
     color: #898781;
   }
   ```

   O `max-width` nos seletores `.grafico-bp svg` / `.grafico-dre svg` não é
   cosmético: ele casa com a largura do `viewBox` de cada gráfico, de modo que
   1 unidade do SVG renderize como 1 pixel de CSS e as barras saiam com os 24px
   especificados em vez de esticarem com o contêiner.

2. Rode o build a partir de `frontend/`:

   ```
   cd frontend && npm install && npm run build
   ```

   (Se `node_modules` já existir, `npm install` é rápido e inofensivo.)
   Esperado: o Vite termina com `✓ built in …` e sai com código 0. Nenhum aviso
   novo sobre CSS.

3. Commit:

   ```
   git add frontend/src/index.css
   git commit -m "Adiciona classes de CSS para os gráficos de BP e DRE"
   ```

---

## Tarefa 2 — Gráfico do Balanço Patrimonial (barras empilhadas comparativas)

### Files

- `frontend/src/components/GraficoBalanco.jsx` — **Create** (o diretório
  `frontend/src/components/` ainda não existe; crie-o)
- `frontend/src/pages/BalancoPatrimonial.jsx` — **Modify**

### Interfaces

**Consome** — classes de CSS já definidas em `frontend/src/index.css`:
`.grafico`, `.grafico-bp`, `.grafico-subtitulo`, `.grafico-legenda`,
`.grafico-legenda-cor`, `.grafico-vazio`, e a classe pré-existente `.erro`
(`color: #b91c1c`). Não redefina nenhuma delas; não edite `index.css` nesta
tarefa.

**Consome** — o objeto de resposta de `GET /relatorios/bp`, que a página já
carrega via `getBP()` de `../api` e guarda no estado `bp`. Forma exata:

```json
{
  "ativo": [
    {"grupo": "Ativo Circulante",
     "contas": [{"codigo": "1.1.01", "nome": "Caixa", "saldo": 1000.0}],
     "subtotal": 4800.0}
  ],
  "passivo_pl": [
    {"grupo": "Passivo Circulante", "contas": [], "subtotal": 2000.0}
  ],
  "total_ativo": 4800.0,
  "total_passivo_pl": 4800.0,
  "balanceado": true
}
```

Garantias da API: `ativo` tem **sempre exatamente 2** seções, nesta ordem —
`"Ativo Circulante"`, `"Ativo Não Circulante"`. `passivo_pl` tem **sempre
exatamente 3**, nesta ordem — `"Passivo Circulante"`, `"Passivo Não Circulante"`,
`"Patrimônio Líquido"`. As seções existem mesmo quando vazias (`subtotal: 0.0`).
A seção `"Patrimônio Líquido"` contém uma conta sintética de `codigo:
"RESULTADO"` carregando o resultado do período — o componente **não** usa a lista
`contas`, apenas `grupo` e `subtotal`.

**Produz:**

- `frontend/src/components/GraficoBalanco.jsx` com `export default function
  GraficoBalanco({ bp })` — recebe o objeto de resposta inteiro em uma única prop
  chamada `bp` e devolve um `<div className="grafico grafico-bp">`.

### Steps

1. Crie o diretório `frontend/src/components/` e, dentro dele, o arquivo
   `GraficoBalanco.jsx` com exatamente este conteúdo:

   ```jsx
   const VIEW_W = 420;
   const VIEW_H = 300;
   const PAD_TOP = 32;
   const BASELINE_Y = 252;
   const PLOT_H = BASELINE_Y - PAD_TOP; // 220
   const BAR_W = 24;
   const VAO = 2;
   const RAIO = 4;
   const CENTROS = [140, 280];

   const SUPERFICIE = "#fcfcfb";
   const PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"];
   const COR_NEUTRA = "#898781";
   const COR_EIXO = "#c3c2b7";
   const COR_TEXTO = "#0b0b0b";
   const COR_TEXTO_SEC = "#52514e";

   const formatador = new Intl.NumberFormat("pt-BR", {
     minimumFractionDigits: 2,
     maximumFractionDigits: 2,
   });

   function fmt(valor) {
     return formatador.format(valor);
   }

   function corDoSlot(indice) {
     return PALETA[indice] || COR_NEUTRA;
   }

   function caminhoTopoArredondado(x, y, largura, altura, raio) {
     const r = Math.min(raio, altura, largura / 2);
     return [
       `M ${x} ${y + altura}`,
       `L ${x} ${y + r}`,
       `Q ${x} ${y} ${x + r} ${y}`,
       `L ${x + largura - r} ${y}`,
       `Q ${x + largura} ${y} ${x + largura} ${y + r}`,
       `L ${x + largura} ${y + altura}`,
       "Z",
     ].join(" ");
   }

   export default function GraficoBalanco({ bp }) {
     const secoes = [
       ...bp.ativo.map((secao, i) => ({
         grupo: secao.grupo,
         subtotal: secao.subtotal,
         cor: corDoSlot(i),
         coluna: 0,
       })),
       ...bp.passivo_pl.map((secao, i) => ({
         grupo: secao.grupo,
         subtotal: secao.subtotal,
         cor: corDoSlot(bp.ativo.length + i),
         coluna: 1,
       })),
     ];

     const barras = [
       {
         rotulo: "Ativo",
         centro: CENTROS[0],
         total: bp.total_ativo,
         segmentos: secoes.filter((s) => s.coluna === 0 && s.subtotal > 0),
       },
       {
         rotulo: "Passivo + PL",
         centro: CENTROS[1],
         total: bp.total_passivo_pl,
         segmentos: secoes.filter((s) => s.coluna === 1 && s.subtotal > 0),
       },
     ];

     const somas = barras.map((barra) =>
       barra.segmentos.reduce((acc, s) => acc + s.subtotal, 0)
     );
     const maxValor = Math.max(
       bp.total_ativo,
       bp.total_passivo_pl,
       somas[0],
       somas[1],
       0
     );

     const negativas = secoes.filter((secao) => secao.subtotal < 0);
     const aviso =
       negativas.length > 0
         ? `${negativas
             .map((secao) => `${secao.grupo} negativo (${fmt(secao.subtotal)})`)
             .join("; ")} ${
             negativas.length > 1
               ? "não podem ser representados como segmentos empilhados"
               : "não pode ser representado como segmento empilhado"
           }. As alturas das barras não são comparáveis neste caso; use a tabela abaixo.`
         : null;

     if (maxValor <= 0) {
       return (
         <div className="grafico grafico-bp">
           <h3>Ativo x Passivo + Patrimônio Líquido</h3>
           <p className="grafico-vazio">
             Sem dados para exibir. Lance ou importe lançamentos para ver o gráfico.
           </p>
           {aviso && <p className="erro">{aviso}</p>}
         </div>
       );
     }

     const escala = PLOT_H / maxValor;

     return (
       <div className="grafico grafico-bp">
         <h3>Ativo x Passivo + Patrimônio Líquido</h3>
         <p className="grafico-subtitulo">
           Quando o balanço fecha, as duas barras têm exatamente a mesma altura.
         </p>
         <svg
           viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
           role="img"
           aria-label={`Ativo de ${fmt(bp.total_ativo)} comparado a Passivo mais Patrimônio Líquido de ${fmt(bp.total_passivo_pl)}`}
         >
           <line
             x1={24}
             y1={BASELINE_Y}
             x2={VIEW_W - 24}
             y2={BASELINE_Y}
             stroke={COR_EIXO}
             strokeWidth={1}
           />
           {barras.map((barra, bi) => {
             const x = barra.centro - BAR_W / 2;
             let acumulado = 0;
             const pecas = barra.segmentos.map((segmento, si) => {
               const altura = segmento.subtotal * escala;
               const y = BASELINE_Y - acumulado - altura;
               acumulado += altura;
               return {
                 segmento,
                 y,
                 altura,
                 topo: si === barra.segmentos.length - 1,
               };
             });
             const topoBarra = BASELINE_Y - somas[bi] * escala;

             return (
               <g key={barra.rotulo}>
                 {pecas.map((peca) =>
                   peca.topo ? (
                     <path
                       key={peca.segmento.grupo}
                       d={caminhoTopoArredondado(x, peca.y, BAR_W, peca.altura, RAIO)}
                       fill={peca.segmento.cor}
                     >
                       <title>{`${peca.segmento.grupo}: ${fmt(peca.segmento.subtotal)}`}</title>
                     </path>
                   ) : (
                     <rect
                       key={peca.segmento.grupo}
                       x={x}
                       y={peca.y}
                       width={BAR_W}
                       height={peca.altura}
                       fill={peca.segmento.cor}
                     >
                       <title>{`${peca.segmento.grupo}: ${fmt(peca.segmento.subtotal)}`}</title>
                     </rect>
                   )
                 )}
                 {pecas.slice(0, -1).map((peca) => (
                   <rect
                     key={`vao-${peca.segmento.grupo}`}
                     x={x}
                     y={peca.y - VAO / 2}
                     width={BAR_W}
                     height={VAO}
                     fill={SUPERFICIE}
                   />
                 ))}
                 <text
                   x={barra.centro}
                   y={topoBarra - 8}
                   textAnchor="middle"
                   fontSize={12}
                   fontWeight={600}
                   fill={COR_TEXTO}
                 >
                   {fmt(barra.total)}
                 </text>
                 <text
                   x={barra.centro}
                   y={BASELINE_Y + 20}
                   textAnchor="middle"
                   fontSize={12}
                   fill={COR_TEXTO_SEC}
                 >
                   {barra.rotulo}
                 </text>
               </g>
             );
           })}
         </svg>
         <ul className="grafico-legenda">
           {secoes.map((secao) => (
             <li key={secao.grupo}>
               <span
                 className="grafico-legenda-cor"
                 style={{ background: secao.cor }}
               />
               {secao.grupo} — {fmt(secao.subtotal)}
             </li>
           ))}
         </ul>
         {aviso && <p className="erro">{aviso}</p>}
       </div>
     );
   }
   ```

   Pontos do desenho que **não** devem ser "simplificados" na transcrição:

   - **Escala compartilhada.** Existe uma única `escala`, derivada de `maxValor`,
     usada pelas duas barras. É isso que faz o balanço fechado virar duas barras
     de altura idêntica. Não calcule uma escala por barra.
   - **O vão de 2px não encolhe a barra.** Os segmentos são desenhados com a
     altura cheia e o vão é um retângulo da cor da superfície (`#fcfcfb`)
     desenhado **por cima** da fronteira interna. Se em vez disso você subtraísse
     2px da altura de cada segmento, uma barra de 2 segmentos e outra de 3
     ficariam 2px diferentes mesmo com o balanço fechado — exatamente o que este
     gráfico existe para mostrar.
   - **Cor segue a entidade.** O índice do slot vem da posição da seção nas
     listas da API (que são fixas e sempre presentes), não da posição entre as
     seções que sobraram depois do filtro. Filtrar um grupo zerado não repinta
     os outros.
   - **Rótulo direto apenas nos totais.** Os subtotais de cada segmento vão para
     a legenda e para o `<title>`; não coloque um número dentro de cada segmento.
   - Seções com `subtotal <= 0` não geram segmento (a comparação é `> 0`, não
     `!== 0`: um subtotal negativo produziria um retângulo de altura negativa).
     `maxValor` inclui as somas dos segmentos desenhados justamente para que
     nenhuma barra possa estourar a área do gráfico se isso acontecer.
   - **O aviso de seção negativa (`aviso`) é obrigatório e não é decoração.** Um
     Patrimônio Líquido negativo — prejuízos acumulados maiores que o Capital
     Social, ou seja, insolvência comum, não um caso teórico — é pulado pelo
     filtro `subtotal > 0`, e então a pilha de Passivo + PL soma **mais** que
     `total_passivo_pl`: a barra sai mais alta que a do Ativo mesmo com
     `balanceado: true`. Sem o aviso, o gráfico afirmaria visualmente "não fecha"
     sobre um balanço que fecha — ensinaria algo falso, que é pior que não
     desenhar nada. O aviso é montado a partir das seções realmente puladas
     (`negativas`), nunca com `"Patrimônio Líquido"` escrito à mão: em princípio
     qualquer uma das cinco seções pode ser a negativa, e a frase concorda em
     número (`não pode` / `não podem`) conforme a quantidade.
   - O aviso usa a classe `.erro`, que **já existe** em `frontend/src/index.css`
     (`color: #b91c1c`) e é a mesma usada pelo aviso de desbalanceamento da
     página. Não crie classe nova e não edite `index.css` nesta tarefa.
   - `aviso` é calculado **antes** do `if (maxValor <= 0)` e renderizado nos dois
     ramos — o do estado vazio e o do gráfico desenhado — para que a explicação
     nunca desapareça junto com o gráfico.
   - O texto do aviso usa o sinal negativo que o `Intl.NumberFormat("pt-BR")`
     produz (`-12.500,00`); não troque o caractere à mão.

2. Abra `frontend/src/pages/BalancoPatrimonial.jsx`. Acrescente o import do
   componente logo abaixo do import de `../api`. Substitua:

   ```jsx
   import { getBP } from "../api";
   ```

   por:

   ```jsx
   import { getBP } from "../api";
   import GraficoBalanco from "../components/GraficoBalanco";
   ```

3. No mesmo arquivo, renderize o gráfico **acima** das tabelas — depois do aviso
   de desbalanceamento e antes da `<div>` com as duas colunas. Substitua:

   ```jsx
         <div style={{ display: "flex", gap: "32px" }}>
   ```

   por:

   ```jsx
         <GraficoBalanco bp={bp} />
         <div style={{ display: "flex", gap: "32px" }}>
   ```

   Nada mais na página muda: o componente `Coluna`, as tabelas, os totais e o
   aviso de `!bp.balanceado` ficam idênticos. O caso desbalanceado não recebe
   tratamento especial no gráfico — as duas barras simplesmente saem com alturas
   diferentes, que é a leitura correta.

4. Rode o build a partir de `frontend/`:

   ```
   cd frontend && npm run build
   ```

   Esperado: o Vite termina com `✓ built in …` e sai com código 0, sem erro de
   resolução de módulo para `../components/GraficoBalanco`.

5. Commit:

   ```
   git add frontend/src/components/GraficoBalanco.jsx frontend/src/pages/BalancoPatrimonial.jsx
   git commit -m "Adiciona gráfico de barras empilhadas ao Balanço Patrimonial"
   ```

**A verificação manual no navegador não faz parte desta tarefa** — ela é feita
depois pelo coordenador. Não suba o servidor, não tire screenshot, não adicione
teste automatizado de frontend.

---

## Tarefa 3 — Gráfico da DRE (cascata)

### Files

- `frontend/src/components/GraficoDRE.jsx` — **Create** (se o diretório
  `frontend/src/components/` ainda não existir, crie-o)
- `frontend/src/pages/DRE.jsx` — **Modify**

### Interfaces

**Consome** — classes de CSS já definidas em `frontend/src/index.css`:
`.grafico`, `.grafico-dre`, `.grafico-subtitulo`, `.grafico-legenda`,
`.grafico-legenda-cor`, `.grafico-vazio`. Não redefina nenhuma delas; não edite
`index.css` nesta tarefa.

**Consome** — o objeto de resposta de `GET /relatorios/dre`, que a página já
carrega via `getDRE()` de `../api` e guarda no estado `dre`. Forma exata:

```json
{
  "receitas": [{"codigo": "3.1.01", "nome": "Receita de Vendas", "valor": 17000.0}],
  "despesas": [{"codigo": "4.1.01", "nome": "CMV", "valor": 10000.0}],
  "total_receitas": 20500.0,
  "total_despesas": 14750.0,
  "resultado_periodo": 5750.0
}
```

Garantias da API: `receitas` tem **sempre 2** entradas e `despesas` **sempre 5**,
incluindo as zeradas — por isso a cascata precisa filtrar `valor > 0`.
`resultado_periodo` pode ser negativo (prejuízo), e nesse caso a cascata cruza o
eixo do zero. O componente usa `total_receitas`, `despesas[].nome`,
`despesas[].valor`, `total_despesas` (só no `aria-label`) e `resultado_periodo`;
não usa a lista `receitas` item a item.

**Produz:**

- `frontend/src/components/GraficoDRE.jsx` com `export default function
  GraficoDRE({ dre })` — recebe o objeto de resposta inteiro em uma única prop
  chamada `dre` e devolve um `<div className="grafico grafico-dre">`.

### Steps

1. Crie `frontend/src/components/GraficoDRE.jsx` com exatamente este conteúdo:

   ```jsx
   const VIEW_W = 720;
   const VIEW_H = 430;
   const PAD_LEFT = 32;
   const PAD_RIGHT = 16;
   const PAD_TOP = 28;
   const PAD_BOTTOM = 122;
   const PLOT_W = VIEW_W - PAD_LEFT - PAD_RIGHT; // 672
   const PLOT_H = VIEW_H - PAD_TOP - PAD_BOTTOM; // 280
   const EIXO_X_Y = PAD_TOP + PLOT_H + 30; // 338
   const BAR_W = 24;
   const RAIO = 4;
   const LIMITE_ROTULO = 26;

   const COR_POSITIVO = "#2a78d6";
   const COR_NEGATIVO = "#e34948";
   const COR_EIXO = "#c3c2b7";
   const COR_CONECTOR = "#e1e0d9";
   const COR_TEXTO = "#0b0b0b";
   const COR_TEXTO_SEC = "#52514e";
   const COR_TEXTO_MUDO = "#898781";

   const formatador = new Intl.NumberFormat("pt-BR", {
     minimumFractionDigits: 2,
     maximumFractionDigits: 2,
   });

   function fmt(valor) {
     return formatador.format(valor);
   }

   function encurtar(texto) {
     return texto.length > LIMITE_ROTULO
       ? `${texto.slice(0, LIMITE_ROTULO - 1)}…`
       : texto;
   }

   function caminhoBarra(x, y, largura, altura, raio, arredondarTopo) {
     const r = Math.min(raio, altura, largura / 2);
     if (arredondarTopo) {
       return [
         `M ${x} ${y + altura}`,
         `L ${x} ${y + r}`,
         `Q ${x} ${y} ${x + r} ${y}`,
         `L ${x + largura - r} ${y}`,
         `Q ${x + largura} ${y} ${x + largura} ${y + r}`,
         `L ${x + largura} ${y + altura}`,
         "Z",
       ].join(" ");
     }
     return [
       `M ${x} ${y}`,
       `L ${x} ${y + altura - r}`,
       `Q ${x} ${y + altura} ${x + r} ${y + altura}`,
       `L ${x + largura - r} ${y + altura}`,
       `Q ${x + largura} ${y + altura} ${x + largura} ${y + altura - r}`,
       `L ${x + largura} ${y}`,
       "Z",
     ].join(" ");
   }

   export default function GraficoDRE({ dre }) {
     const passos = [];
     passos.push({
       rotulo: "Receitas",
       inicio: 0,
       fim: dre.total_receitas,
       valor: dre.total_receitas,
       positivo: true,
     });

     let acumulado = dre.total_receitas;
     dre.despesas
       .filter((despesa) => despesa.valor > 0)
       .forEach((despesa) => {
         passos.push({
           rotulo: despesa.nome,
           inicio: acumulado,
           fim: acumulado - despesa.valor,
           valor: despesa.valor,
           positivo: false,
         });
         acumulado -= despesa.valor;
       });

     passos.push({
       rotulo: "Resultado",
       inicio: 0,
       fim: dre.resultado_periodo,
       valor: dre.resultado_periodo,
       positivo: dre.resultado_periodo >= 0,
     });

     const valores = passos
       .flatMap((passo) => [passo.inicio, passo.fim])
       .concat(0);
     const maxV = Math.max(...valores);
     const minV = Math.min(...valores);
     const amplitude = maxV - minV;

     if (amplitude <= 0) {
       return (
         <div className="grafico grafico-dre">
           <h3>Cascata do resultado</h3>
           <p className="grafico-vazio">
             Sem dados para exibir. Lance ou importe lançamentos para ver o gráfico.
           </p>
         </div>
       );
     }

     const escala = PLOT_H / amplitude;
     const posY = (valor) => PAD_TOP + (maxV - valor) * escala;
     const zeroY = posY(0);
     const banda = PLOT_W / passos.length;
     const centro = (indice) => PAD_LEFT + banda * (indice + 0.5);

     return (
       <div className="grafico grafico-dre">
         <h3>Cascata do resultado</h3>
         <p className="grafico-subtitulo">
           Da receita total, cada despesa consome uma parte; o que sobra é o
           resultado do período.
         </p>
         <svg
           viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
           role="img"
           aria-label={`Cascata da DRE: receitas de ${fmt(dre.total_receitas)}, despesas de ${fmt(dre.total_despesas)} e resultado do período de ${fmt(dre.resultado_periodo)}`}
         >
           {passos.slice(0, -1).map((passo, i) => (
             <line
               key={`conector-${i}`}
               x1={centro(i) + BAR_W / 2}
               y1={posY(passo.fim)}
               x2={centro(i + 1) - BAR_W / 2}
               y2={posY(passo.fim)}
               stroke={COR_CONECTOR}
               strokeWidth={1}
             />
           ))}
           <line
             x1={PAD_LEFT}
             y1={zeroY}
             x2={VIEW_W - PAD_RIGHT}
             y2={zeroY}
             stroke={COR_EIXO}
             strokeWidth={1}
           />
           <text
             x={PAD_LEFT - 6}
             y={zeroY + 4}
             textAnchor="end"
             fontSize={10}
             fill={COR_TEXTO_MUDO}
           >
             0
           </text>
           {passos.map((passo, i) => {
             const vAlto = Math.max(passo.inicio, passo.fim);
             const vBaixo = Math.min(passo.inicio, passo.fim);
             const yTopo = posY(vAlto);
             const altura = (vAlto - vBaixo) * escala;
             const cresce = passo.fim >= passo.inicio;
             const cor = passo.positivo ? COR_POSITIVO : COR_NEGATIVO;
             const rotuloValor =
               (passo.positivo ? "" : "−") + fmt(Math.abs(passo.valor));
             const yRotulo = cresce ? yTopo - 6 : yTopo + altura + 14;

             return (
               <g key={`passo-${i}`}>
                 {altura >= 0.5 && (
                   <path
                     d={caminhoBarra(
                       centro(i) - BAR_W / 2,
                       yTopo,
                       BAR_W,
                       altura,
                       RAIO,
                       cresce
                     )}
                     fill={cor}
                   >
                     <title>{`${passo.rotulo}: ${rotuloValor}`}</title>
                   </path>
                 )}
                 <text
                   x={centro(i)}
                   y={yRotulo}
                   textAnchor="middle"
                   fontSize={11}
                   fontWeight={600}
                   fill={COR_TEXTO}
                 >
                   {rotuloValor}
                 </text>
                 <text
                   x={centro(i)}
                   y={EIXO_X_Y}
                   textAnchor="end"
                   fontSize={11}
                   fill={COR_TEXTO_SEC}
                   transform={`rotate(-30 ${centro(i)} ${EIXO_X_Y})`}
                 >
                   {encurtar(passo.rotulo)}
                 </text>
               </g>
             );
           })}
         </svg>
         <ul className="grafico-legenda">
           <li>
             <span
               className="grafico-legenda-cor"
               style={{ background: COR_POSITIVO }}
             />
             Aumenta o resultado
           </li>
           <li>
             <span
               className="grafico-legenda-cor"
               style={{ background: COR_NEGATIVO }}
             />
             Reduz o resultado
           </li>
         </ul>
       </div>
     );
   }
   ```

   Pontos do desenho que **não** devem ser "simplificados" na transcrição:

   - **O domínio sempre inclui o zero.** `valores` termina com `.concat(0)`, então
     `minV <= 0 <= maxV`. É isso que garante que a linha do zero esteja sempre
     visível e que uma cascata que mergulha no prejuízo caiba inteira na área do
     gráfico. Barras abaixo do zero são desenhadas normalmente porque a altura é
     sempre `(vAlto - vBaixo) * escala`, um número não-negativo, e o topo é
     `posY(vAlto)` — a aritmética não muda de sinal quando os valores mudam.
   - **Estado vazio antes da divisão.** O `if (amplitude <= 0)` vem **antes** de
     `const escala = PLOT_H / amplitude`. Com o razão vazio, todos os `inicio` e
     `fim` são 0, `amplitude` é 0 e o componente devolve a mensagem em vez de
     dividir por zero.
   - **A barra final ancora no zero**, não no acumulado: `inicio: 0, fim:
     dre.resultado_periodo`. Ela é um total, não mais um passo da cascata. O
     conector que chega nela vem do fim da última despesa, que é exatamente o
     mesmo nível de valor — é esse encontro que fecha a leitura.
   - **A cor da barra final vem do sinal** de `resultado_periodo` (`>= 0` →
     `#2a78d6`, senão `#e34948`), usando o mesmo par divergente das demais barras:
     azul é o que soma, vermelho é o que subtrai. Não use cores de status.
   - **O sinal também aparece no texto** (`−` U+2212 antes do valor das despesas e
     de um prejuízo), então a direção nunca depende só da cor.
   - **A ponta de dados arredondada segue a direção**: `cresce` decide se o
     arredondamento de 4px vai no topo (barra que sobe) ou na base (barra que
     desce). O mesmo `cresce` decide se o rótulo de valor fica acima do topo ou
     abaixo da base, para que ele acompanhe a ponta da barra.
   - Despesas com `valor > 0` apenas: a API sempre devolve as 5 contas de despesa,
     inclusive zeradas, e uma barra de altura zero na cascata seria uma coluna
     morta.

2. Abra `frontend/src/pages/DRE.jsx`. Acrescente o import do componente logo
   abaixo do import de `../api`. Substitua:

   ```jsx
   import { getDRE } from "../api";
   ```

   por:

   ```jsx
   import { getDRE } from "../api";
   import GraficoDRE from "../components/GraficoDRE";
   ```

3. No mesmo arquivo, renderize o gráfico **acima** das tabelas — logo depois do
   `<h2>`. Substitua:

   ```jsx
         <h2>Demonstração de Resultado do Exercício</h2>

         <h3>Receitas</h3>
   ```

   por:

   ```jsx
         <h2>Demonstração de Resultado do Exercício</h2>

         <GraficoDRE dre={dre} />

         <h3>Receitas</h3>
   ```

   Nada mais na página muda: as duas tabelas, os totais e a linha de resultado do
   período ficam idênticos.

4. Rode o build a partir de `frontend/`:

   ```
   cd frontend && npm run build
   ```

   Esperado: o Vite termina com `✓ built in …` e sai com código 0, sem erro de
   resolução de módulo para `../components/GraficoDRE`.

5. Commit:

   ```
   git add frontend/src/components/GraficoDRE.jsx frontend/src/pages/DRE.jsx
   git commit -m "Adiciona gráfico em cascata à DRE"
   ```

**A verificação manual no navegador não faz parte desta tarefa** — ela é feita
depois pelo coordenador. Não suba o servidor, não tire screenshot, não adicione
teste automatizado de frontend.

---

## Verificação manual (para o coordenador, depois das três tarefas)

Fixture: `lancamentos_exemplo.csv` na raiz do repositório (18 lançamentos),
importado pela aba Lançamentos sobre um banco recém-semeado.

Valores que essa fixture produz, conferidos contra o CSV e o plano de contas em
`backend/app/seed.py`:

- **BP** — Ativo Circulante 71.750,00 (Caixa 4.500,00 + Bancos 52.250,00 +
  Clientes 6.000,00 + Estoques 9.000,00); Ativo Não Circulante 8.000,00;
  **total do ativo 79.750,00**. Passivo Circulante 34.000,00 (Fornecedores
  5.000,00 + Empréstimos CP 20.000,00 + Salários a Pagar 9.000,00 + Impostos a
  Pagar 0,00); Passivo Não Circulante **0,00**; Patrimônio Líquido 45.750,00
  (Capital Social 50.000,00 + resultado −4.250,00); **total do passivo + PL
  79.750,00**.
- **DRE** — total de receitas 20.500,00 (Vendas 17.000,00 + Serviços 3.500,00);
  despesas CMV 10.000,00, Administrativas 11.200,00, com Vendas 1.500,00,
  Financeiras 250,00, Impostos sobre Vendas 1.800,00; total de despesas
  24.750,00; **resultado do período −4.250,00 (prejuízo)**.

Checklist:

- [ ] Aba Balanço Patrimonial: as duas barras têm exatamente a mesma altura
      (79.750,00 dos dois lados), com o topo de cada uma rotulado.
- [ ] A barra de Passivo + PL tem **dois** segmentos, não três — Passivo Não
      Circulante está zerado e não gera segmento. A legenda ainda lista os cinco
      grupos, e o de Passivo Não Circulante mostra `0,00`.
- [ ] Há um vão branco de 2px entre segmentos empilhados, sem borda desenhada.
- [ ] Aba DRE: sete barras — Receitas, as cinco despesas e Resultado.
- [ ] A cascata cruza a linha do zero: a barra de Resultado desce abaixo do zero,
      em vermelho, rotulada `−4.250,00`.
- [ ] O conector que sai da última despesa encontra a barra de Resultado no mesmo
      nível de valor.
- [ ] Passar o mouse sobre qualquer barra mostra o tooltip com nome e valor.
- [ ] As tabelas das duas páginas continuam exatamente como antes, abaixo dos
      gráficos.
- [ ] Zerar o banco (base recém-criada, sem lançamentos): as duas páginas mostram
      a mensagem de estado vazio no lugar do gráfico, sem erro no console.
- [ ] Patrimônio Líquido negativo: sobre a fixture, lançar despesas suficientes
      para que o prejuízo acumulado ultrapasse o Capital Social (por exemplo,
      débito `4.1.02` / crédito `1.1.02` de 100.000,00). O segmento de PL some da
      barra de Passivo + PL, as duas barras ficam com alturas diferentes, e
      aparece sob a legenda, em vermelho, o aviso nomeando o grupo e o valor:
      `Patrimônio Líquido negativo (-…) não pode ser representado como segmento
      empilhado. As alturas das barras não são comparáveis neste caso; use a
      tabela abaixo.` A tabela abaixo continua mostrando o subtotal negativo
      correto.
- [ ] `cd backend && pytest -v` continua com 20 testes passando (nada de backend
      foi tocado, é só a confirmação).
