import { useEffect, useState } from "react";
import { getUsuarios, criarUsuario } from "../api";

const USUARIO_VAZIO = {
  email: "",
  nome: "",
  senha: "",
  papel: "comum",
};

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [form, setForm] = useState(USUARIO_VAZIO);
  const [erroForm, setErroForm] = useState(null);

  async function carregarDados() {
    setUsuarios(await getUsuarios());
  }

  useEffect(() => {
    carregarDados().catch((e) => setErroForm(e.message));
  }, []);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErroForm(null);
    try {
      await criarUsuario(form);
      setForm(USUARIO_VAZIO);
      await carregarDados();
    } catch (erro) {
      // Erro mantém os campos como estavam, para poder corrigir o e-mail e
      // tentar de novo.
      setErroForm(erro.message);
    }
  }

  return (
    <section>
      <h2>Usuários</h2>

      <form className="form-lancamento" onSubmit={aoSubmeter}>
        <label className="campo">
          <span className="campo-rotulo">E-mail</span>
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Nome</span>
          <input
            type="text"
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Senha</span>
          <input
            type="password"
            value={form.senha}
            onChange={(e) => setForm({ ...form, senha: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Papel</span>
          <select
            value={form.papel}
            onChange={(e) => setForm({ ...form, papel: e.target.value })}
          >
            <option value="comum">comum</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <button type="submit" className="botao">
          Criar usuário
        </button>
      </form>
      {erroForm && <p className="erro">{erroForm}</p>}

      <h3>Usuários existentes</h3>
      <div className="tabela-rolagem">
        <table>
          <thead>
            <tr>
              <th>E-mail</th>
              <th>Nome</th>
              <th>Papel</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((usuario) => (
              <tr key={usuario.id}>
                <td>{usuario.email}</td>
                <td>{usuario.nome}</td>
                <td>{usuario.papel}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
