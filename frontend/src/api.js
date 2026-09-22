const API_BASE = "http://localhost:8000";
const CHAVE_TOKEN = "token";

export function getToken() {
  return localStorage.getItem(CHAVE_TOKEN);
}

export function limparToken() {
  localStorage.removeItem(CHAVE_TOKEN);
}

// Monta os cabeçalhos de uma chamada autenticada. `extras` recebe o
// Content-Type das chamadas com corpo JSON; o upload de arquivo não passa
// nada, porque quem monta o boundary do multipart é o próprio browser — e
// fixar Content-Type ali quebraria o upload.
function cabecalhos(extras = {}) {
  const token = getToken();
  return token ? { ...extras, Authorization: `Bearer ${token}` } : { ...extras };
}

async function handleResponse(resposta) {
  // Token ausente, inválido ou expirado no meio do uso: limpa e recarrega,
  // o que devolve o app à tela de login. Sem isto, a sessão vencida vira uma
  // mensagem de erro que o usuário não tem como resolver na tela em que está.
  if (resposta.status === 401) {
    limparToken();
    window.location.reload();
    throw new Error("Sessão expirada");
  }
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

// login NÃO passa por handleResponse de propósito: ali, 401 significa "senha
// errada" e tem de virar mensagem na tela, não recarregar a página.
export async function login(email, senha) {
  const resposta = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });
  if (resposta.status === 401) {
    throw new Error("E-mail ou senha inválidos");
  }
  if (!resposta.ok) {
    throw new Error(`Erro ${resposta.status}`);
  }
  const corpo = await resposta.json();
  localStorage.setItem(CHAVE_TOKEN, corpo.token);
  return corpo;
}

// getMe também fica fora de handleResponse: é chamada na abertura da página,
// e recarregar em resposta a um token velho faria o app piscar antes de cair
// no login. Quem chama (App.jsx) limpa o token e mostra o login direto.
export async function getMe() {
  const resposta = await fetch(`${API_BASE}/me`, { headers: cabecalhos() });
  if (!resposta.ok) {
    throw new Error("Sessão inválida");
  }
  return resposta.json();
}

export function getUsuarios() {
  return fetch(`${API_BASE}/usuarios`, { headers: cabecalhos() }).then(handleResponse);
}

export function criarUsuario(dados) {
  return fetch(`${API_BASE}/usuarios`, {
    method: "POST",
    headers: cabecalhos({ "Content-Type": "application/json" }),
    body: JSON.stringify(dados),
  }).then(handleResponse);
}

export function getContas() {
  return fetch(`${API_BASE}/contas`, { headers: cabecalhos() }).then(handleResponse);
}

export function getLancamentos() {
  return fetch(`${API_BASE}/lancamentos`, { headers: cabecalhos() }).then(handleResponse);
}

export function criarLancamento(lancamento) {
  return fetch(`${API_BASE}/lancamentos`, {
    method: "POST",
    headers: cabecalhos({ "Content-Type": "application/json" }),
    body: JSON.stringify(lancamento),
  }).then(handleResponse);
}

// `dados` é { data, historico }: contas e valor não vão no corpo — o backend
// os deriva do lançamento original, invertendo os dois lados.
export function estornarLancamento(id, dados) {
  return fetch(`${API_BASE}/lancamentos/${id}/estorno`, {
    method: "POST",
    headers: cabecalhos({ "Content-Type": "application/json" }),
    body: JSON.stringify(dados),
  }).then(handleResponse);
}

export function uploadLancamentos(arquivo) {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  return fetch(`${API_BASE}/lancamentos/upload`, {
    method: "POST",
    headers: cabecalhos(),
    body: formData,
  }).then(handleResponse);
}

export function getBalancete() {
  return fetch(`${API_BASE}/relatorios/balancete`, { headers: cabecalhos() }).then(handleResponse);
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
    `${API_BASE}/relatorios/bp${querystring({ data_corte: dataCorte })}`,
    { headers: cabecalhos() }
  ).then(handleResponse);
}

export function getDRE(dataInicio, dataFim) {
  return fetch(
    `${API_BASE}/relatorios/dre${querystring({ data_inicio: dataInicio, data_fim: dataFim })}`,
    { headers: cabecalhos() }
  ).then(handleResponse);
}

export function getDFC() {
  return fetch(`${API_BASE}/relatorios/dfc`, { headers: cabecalhos() }).then(handleResponse);
}

export function getAnalise() {
  return fetch(`${API_BASE}/relatorios/analise`, { headers: cabecalhos() }).then(handleResponse);
}

// As três rotas de exportação devolvem xlsx binário; handleResponse não
// serve para elas, porque termina sempre em resposta.json(). O corpo de
// ERRO dessas rotas, porém, continua sendo o JSON {"detail": ...} do
// FastAPI — então o caminho de erro aqui é o mesmo de handleResponse,
// repetido de propósito, e só o caminho de sucesso muda para .blob().
async function handleResponseArquivo(resposta) {
  if (resposta.status === 401) {
    limparToken();
    window.location.reload();
    throw new Error("Sessão expirada");
  }
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    const detalhe = corpo.detail;
    const mensagem = Array.isArray(detalhe)
      ? detalhe.map((erro) => `${(erro.loc || []).slice(1).join(".")}: ${erro.msg}`).join("; ")
      : detalhe;
    throw new Error(mensagem || `Erro ${resposta.status}`);
  }
  return resposta.blob();
}

// Salvar o blob é o preço de buscar o arquivo por fetch: como a requisição
// não é mais uma navegação do browser, o download tem de ser disparado na
// mão. Âncora sintética, clique programático e revoke logo depois — sem o
// revoke, cada exportação deixa o xlsx inteiro preso na memória da aba até
// o próximo reload.
export function salvarArquivo(blob, nomeArquivo) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeArquivo;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function getBalancetePlanilha() {
  return fetch(`${API_BASE}/relatorios/balancete/exportar`, {
    headers: cabecalhos(),
  }).then(handleResponseArquivo);
}

export function getBPPlanilha() {
  return fetch(`${API_BASE}/relatorios/bp/exportar`, {
    headers: cabecalhos(),
  }).then(handleResponseArquivo);
}

export function getDREPlanilha() {
  return fetch(`${API_BASE}/relatorios/dre/exportar`, {
    headers: cabecalhos(),
  }).then(handleResponseArquivo);
}
