const API_BASE = "http://localhost:8000";

async function handleResponse(resposta) {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    throw new Error(corpo.detail || `Erro ${resposta.status}`);
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

export function getBP() {
  return fetch(`${API_BASE}/relatorios/bp`).then(handleResponse);
}

export function getDRE() {
  return fetch(`${API_BASE}/relatorios/dre`).then(handleResponse);
}
