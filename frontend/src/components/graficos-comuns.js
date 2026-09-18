// Vocabulário compartilhado de apresentação: formatação de número, cores de
// chrome/tinta e geometria de barra. Os gráficos de BP e DRE usam tudo; a
// página de Análise usa só o fmt. Não abstrai a estrutura dos gráficos em si —
// cada um mantém seu próprio layout, eixos e legenda.

export const BAR_W = 24;
export const RAIO = 4;

export const COR_EIXO = "#c3c2b7";
export const COR_TEXTO = "#0b0b0b";
export const COR_TEXTO_SEC = "#52514e";
export const COR_TEXTO_MUDO = "#898781";

const formatador = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function fmt(valor) {
  return formatador.format(valor);
}

export const MENSAGEM_VAZIO =
  "Sem dados para exibir. Lance ou importe lançamentos para ver o gráfico.";

export function caminhoBarra(x, y, largura, altura, raio, arredondarTopo) {
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
