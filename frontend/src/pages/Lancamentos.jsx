import { useEffect, useState } from "react";
import { getContas, getLancamentos, criarLancamento, uploadLancamentos } from "../api";

const LANCAMENTO_VAZIO = {
  data: "",
  conta_debito: "",
  conta_credito: "",
  valor: "",
  historico: "",
};

export default function Lancamentos() {
  const [contas, setContas] = useState([]);
  const [lancamentos, setLancamentos] = useState([]);
  const [form, setForm] = useState(LANCAMENTO_VAZIO);
  const [erroForm, setErroForm] = useState(null);
  const [resultadoUpload, setResultadoUpload] = useState(null);

  async function carregarDados() {
    const [contasResp, lancamentosResp] = await Promise.all([getContas(), getLancamentos()]);
    setContas(contasResp);
    setLancamentos(lancamentosResp);
  }

  useEffect(() => {
    carregarDados();
  }, []);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErroForm(null);
    try {
      await criarLancamento({ ...form, valor: parseFloat(form.valor) });
      setForm(LANCAMENTO_VAZIO);
      await carregarDados();
    } catch (erro) {
      setErroForm(erro.message);
    }
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

      <form onSubmit={aoSubmeter}>
        <label>
          Data
          <input
            type="date"
            value={form.data}
            onChange={(e) => setForm({ ...form, data: e.target.value })}
            required
          />
        </label>
        <label>
          Conta débito
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
        <label>
          Conta crédito
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
        <label>
          Valor
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={form.valor}
            onChange={(e) => setForm({ ...form, valor: e.target.value })}
            required
          />
        </label>
        <label>
          Histórico
          <input
            type="text"
            value={form.historico}
            onChange={(e) => setForm({ ...form, historico: e.target.value })}
          />
        </label>
        <button type="submit">Lançar</button>
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
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Débito</th>
            <th>Crédito</th>
            <th>Valor</th>
            <th>Histórico</th>
          </tr>
        </thead>
        <tbody>
          {lancamentos.map((lancamento) => (
            <tr key={lancamento.id}>
              <td>{lancamento.data}</td>
              <td>{lancamento.conta_debito}</td>
              <td>{lancamento.conta_credito}</td>
              <td>{lancamento.valor.toFixed(2)}</td>
              <td>{lancamento.historico}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
