import { useEffect, useState } from "react";
import {
  getContas,
  getLancamentos,
  criarLancamento,
  estornarLancamento,
  uploadLancamentos,
} from "../api";
import { fmt, classeValor, formatarData } from "../components/graficos-comuns";

const LANCAMENTO_VAZIO = {
  data: "",
  conta_debito: "",
  conta_credito: "",
  valor: "",
  historico: "",
};

// O mesmo texto que o backend geraria se `historico` fosse enviado vazio
// (_historico_padrao_estorno, em routers/lancamentos.py). Duplicado de
// propósito: o campo já chega preenchido e editável, sem uma ida ao servidor
// só para descobrir o rótulo padrão.
function historicoPadraoEstorno(lancamento) {
  return lancamento.historico
    ? `Estorno do lançamento #${lancamento.id}: ${lancamento.historico}`
    : `Estorno do lançamento #${lancamento.id}`;
}

// id do original -> id do estorno que aponta para ele. Nada impede dois
// estornos do mesmo lançamento (o app não valida duplicidade em lugar
// nenhum); nesse caso a indicação cita o de menor id — determinístico
// independente da ordem da lista, que vem ordenada por data.
function mapearEstornos(lancamentos) {
  const mapa = {};
  lancamentos.forEach((lancamento) => {
    if (lancamento.estorno_de == null) return;
    const atual = mapa[lancamento.estorno_de];
    if (atual === undefined || lancamento.id < atual) {
      mapa[lancamento.estorno_de] = lancamento.id;
    }
  });
  return mapa;
}

export default function Lancamentos() {
  const [contas, setContas] = useState([]);
  const [lancamentos, setLancamentos] = useState([]);
  const [form, setForm] = useState(LANCAMENTO_VAZIO);
  const [estornoDe, setEstornoDe] = useState(null);
  const [erroForm, setErroForm] = useState(null);
  const [resultadoUpload, setResultadoUpload] = useState(null);

  const emModoEstorno = estornoDe !== null;
  const estornadoPor = mapearEstornos(lancamentos);

  async function carregarDados() {
    const [contasResp, lancamentosResp] = await Promise.all([getContas(), getLancamentos()]);
    setContas(contasResp);
    setLancamentos(lancamentosResp);
  }

  useEffect(() => {
    carregarDados().catch((e) => setErroForm(e.message));
  }, []);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErroForm(null);
    try {
      if (emModoEstorno) {
        // Contas e valor não vão: o backend os deriva do original.
        await estornarLancamento(estornoDe, { data: form.data, historico: form.historico });
        setEstornoDe(null);
      } else {
        await criarLancamento({ ...form, valor: parseFloat(form.valor) });
      }
      setForm(LANCAMENTO_VAZIO);
      await carregarDados();
    } catch (erro) {
      // Erro mantém o modo e os campos como estavam, para poder corrigir a
      // data e tentar de novo.
      setErroForm(erro.message);
    }
  }

  function aoEstornar(lancamento) {
    setErroForm(null);
    setEstornoDe(lancamento.id);
    setForm({
      data: "",
      conta_debito: lancamento.conta_credito,
      conta_credito: lancamento.conta_debito,
      valor: String(lancamento.valor),
      historico: historicoPadraoEstorno(lancamento),
    });
  }

  function aoCancelarEstorno() {
    setErroForm(null);
    setEstornoDe(null);
    setForm(LANCAMENTO_VAZIO);
  }

  async function aoSelecionarArquivo(evento) {
    const arquivo = evento.target.files[0];
    if (!arquivo) return;
    setErroForm(null);
    try {
      const resultado = await uploadLancamentos(arquivo);
      setResultadoUpload(resultado);
      await carregarDados();
    } catch (erro) {
      setErroForm(erro.message);
    }
    evento.target.value = "";
  }

  return (
    <section>
      <h2>Lançamentos</h2>

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
            disabled={emModoEstorno}
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
            disabled={emModoEstorno}
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
            disabled={emModoEstorno}
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
          {emModoEstorno ? "Confirmar estorno" : "Lançar"}
        </button>
        {emModoEstorno && (
          <button type="button" className="botao" onClick={aoCancelarEstorno}>
            Cancelar
          </button>
        )}
      </form>
      {erroForm && <p className="erro">{erroForm}</p>}

      <h3>Importar CSV</h3>
      <p>Colunas esperadas: data, conta_debito, conta_credito, valor, historico</p>
      <input type="file" accept=".csv" onChange={aoSelecionarArquivo} />
      {resultadoUpload && (
        <div>
          <p>{resultadoUpload.inseridos} lançamento(s) inserido(s).</p>
          {resultadoUpload.erros.length > 0 && (
            <ul className="erro">
              {resultadoUpload.erros.map((erro) => (
                <li key={erro.linha}>
                  Linha {erro.linha}: {erro.motivo}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

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
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {lancamentos.map((lancamento) => (
              <tr key={lancamento.id}>
                <td>{formatarData(lancamento.data)}</td>
                <td>{lancamento.conta_debito}</td>
                <td>{lancamento.conta_credito}</td>
                <td className={classeValor(lancamento.valor)}>
                  {fmt(lancamento.valor)}
                </td>
                <td>
                  {lancamento.historico}
                  {lancamento.estorno_de != null &&
                    ` (estorno do lançamento #${lancamento.estorno_de})`}
                  {estornadoPor[lancamento.id] !== undefined &&
                    ` (estornado pelo lançamento #${estornadoPor[lancamento.id]})`}
                </td>
                <td>
                  <button
                    type="button"
                    className="botao"
                    onClick={() => aoEstornar(lancamento)}
                  >
                    Estornar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
