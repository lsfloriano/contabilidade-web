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

// Vermelho é reservado a valores negativos e recusas. Toda célula de dinheiro
// passa por aqui, inclusive as que nunca deveriam ser negativas: se um negativo
// aparecer onde não se esperava, ele aparece em vermelho em vez de passar
// despercebido.
export function classeValor(valor) {
  return valor < 0 ? "razao-valor valor-negativo" : "razao-valor";
}
