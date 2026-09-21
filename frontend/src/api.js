const API_BASE = "http://localhost:8000";

async function handleResponse(resposta) {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    const detalhe = corpo.detail;
    const mensagem = Array.isArray(detalhe)
      ? detalhe.map((erro) => `${(erro.loc || []).slice(1).join(".")}: ${erro.msg}`).join("; ")
      : detalhe;
    throw new Error(mensagem || `Erro ${resposta.status}`);
  }
  return resposta.json();
}

export function getContas() {
  return fetch(`${API_BASE}/contas`).then(handleResponse);
}

export function getLancamentos() {
  return fetch(`${API_BASE}/lancamentos`).then(handleResponse);
}

export function criarLancamento(lancamento) {
  return fetch(`${API_BASE}/lancamentos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lancamento),
  }).then(handleResponse);
}

// `dados` é { data, historico }: contas e valor não vão no corpo — o backend
// os deriva do lançamento original, invertendo os dois lados.
export function estornarLancamento(id, dados) {
  return fetch(`${API_BASE}/lancamentos/${id}/estorno`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  }).then(handleResponse);
}

export function uploadLancamentos(arquivo) {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  return fetch(`${API_BASE}/lancamentos/upload`, {
    method: "POST",
    body: formData,
  }).then(handleResponse);
}

export function getBalancete() {
  return fetch(`${API_BASE}/relatorios/balancete`).then(handleResponse);
}

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

export function getDFC() {
  return fetch(`${API_BASE}/relatorios/dfc`).then(handleResponse);
}

export function getAnalise() {
  return fetch(`${API_BASE}/relatorios/analise`).then(handleResponse);
}
