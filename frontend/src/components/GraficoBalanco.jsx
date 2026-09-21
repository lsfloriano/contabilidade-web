import {
  BAR_W,
  RAIO,
  COR_EIXO,
  COR_TEXTO,
  COR_TEXTO_SEC,
  fmt,
  MENSAGEM_VAZIO,
  caminhoBarra,
  arredondar,
} from "./graficos-comuns";

const VIEW_W = 420;
const VIEW_H = 300;
const PAD_TOP = 32;
const BASELINE_Y = 252;
const PLOT_H = BASELINE_Y - PAD_TOP; // 220
const VAO = 2;
const CENTROS = [140, 280];

// Tem de acompanhar --papel em index.css: é a cor por trás dos vãos entre
// segmentos empilhados, e uma divergência aparece como faixas claras entre eles.
const SUPERFICIE = "#fcfcfb";
// Paleta categorica puxada para perto do papel: tinta impressa, nao tela.
// Validada em contraste (todas >= 3.0 contra --papel) e em dicromacia. O par
// dificil e Passivo Circulante vs Patrimonio Liquido sob deuteranopia; eles se
// separam por claridade (L* ~58 contra ~28), nao por matiz, que e o que sobra
// quando o eixo vermelho-verde some. Se mexer numa destas, revalide: a paleta
// saturada anterior tinha tres cores abaixo de 3.0 e esse par em deltaE 13.
//
// Os cinco nunca aparecem juntos — a barra do Ativo empilha os dois primeiros,
// a de Passivo+PL os tres ultimos —, entao so pares dentro da mesma pilha
// precisam ser distinguiveis.
const PALETA = ["#3f5f8a", "#9e5535", "#5a9a94", "#8a7a33", "#5e3a4c"];

function corDoSlot(indice) {
  return PALETA[indice];
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

  const negativas = secoes.filter((secao) => arredondar(secao.subtotal) < 0);
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
        <p className="grafico-vazio">{MENSAGEM_VAZIO}</p>
        {aviso && <p className="grafico-aviso">{aviso}</p>}
      </div>
    );
  }

  const escala = PLOT_H / maxValor;

  return (
    <div className="grafico grafico-bp">
      <h3>Ativo x Passivo + Patrimônio Líquido</h3>
      <p className="grafico-subtitulo">
        {aviso
          ? "Com uma seção negativa, as alturas das barras deixam de ser comparáveis."
          : "Quando o balanço fecha, as duas barras têm exatamente a mesma altura."}
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
                    d={caminhoBarra(x, peca.y, BAR_W, peca.altura, RAIO, true)}
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
            {secao.grupo} (
            {secao.coluna === 0 ? "Ativo" : "Passivo + PL"}) —{" "}
            {fmt(secao.subtotal)}
          </li>
        ))}
      </ul>
      {aviso && <p className="grafico-aviso">{aviso}</p>}
    </div>
  );
}
