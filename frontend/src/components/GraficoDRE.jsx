import {
  BAR_W,
  RAIO,
  COR_EIXO,
  COR_TEXTO,
  COR_TEXTO_SEC,
  COR_TEXTO_MUDO,
  fmt,
  MENSAGEM_VAZIO,
  caminhoBarra,
} from "./graficos-comuns";

const VIEW_W = 720;
const VIEW_H = 430;
const PAD_LEFT = 32;
const PAD_RIGHT = 16;
const PAD_TOP = 28;
const PAD_BOTTOM = 122;
const PLOT_W = VIEW_W - PAD_LEFT - PAD_RIGHT; // 672
const PLOT_H = VIEW_H - PAD_TOP - PAD_BOTTOM; // 280
const EIXO_X_Y = PAD_TOP + PLOT_H + 30; // 338
const LIMITE_ROTULO = 26;

const COR_POSITIVO = "#2a78d6";
const COR_NEGATIVO = "#e34948";
const COR_CONECTOR = "#e1e0d9";

function encurtar(texto) {
  return texto.length > LIMITE_ROTULO
    ? `${texto.slice(0, LIMITE_ROTULO - 1)}…`
    : texto;
}

export default function GraficoDRE({ dre }) {
  const passos = [];
  passos.push({
    rotulo: "Receitas",
    inicio: 0,
    fim: dre.total_receitas,
    valor: dre.total_receitas,
    positivo: dre.total_receitas >= 0,
  });

  let acumulado = dre.total_receitas;
  const despesasNegativas = dre.despesas.filter((despesa) => despesa.valor < 0);
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

  const aviso =
    despesasNegativas.length > 0
      ? `${despesasNegativas
          .map((despesa) => `${despesa.nome} negativa (${fmt(despesa.valor)})`)
          .join("; ")} ${
          despesasNegativas.length > 1
            ? "não podem ser representadas na cascata"
            : "não pode ser representada na cascata"
        }. O total acumulado após as despesas não corresponde ao resultado do período; use a tabela abaixo.`
      : null;

  if (amplitude <= 0) {
    return (
      <div className="grafico grafico-dre">
        <h3>Cascata do resultado</h3>
        <p className="grafico-vazio">{MENSAGEM_VAZIO}</p>
        {aviso && <p className="grafico-aviso">{aviso}</p>}
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
      {aviso && <p className="grafico-aviso">{aviso}</p>}
    </div>
  );
}
