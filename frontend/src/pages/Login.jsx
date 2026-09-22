import { useState } from "react";
import { login } from "../api";

// As credenciais ficam à vista de propósito: é ambiente de demonstração, e
// sem cadastro público nem recuperação de senha ninguém entraria sozinho.
const CREDENCIAIS_DE_TESTE = [
  "admin@contabilidade.com / admin123 (administrador)",
  "teste1@contabilidade.com / teste123",
  "teste2@contabilidade.com / teste123",
];

export default function Login({ aoEntrar }) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const usuario = await login(email, senha);
      aoEntrar(usuario);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="tela-login">
      <h2>Contabilidade Web</h2>

      <form className="form-lancamento" onSubmit={aoSubmeter}>
        <label className="campo">
          <span className="campo-rotulo">E-mail</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Senha</span>
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
          />
        </label>
        <button type="submit" className="botao" disabled={enviando}>
          {enviando ? "Entrando…" : "Entrar"}
        </button>
      </form>

      {erro && <p className="erro">{erro}</p>}

      <div>
        <p className="campo-rotulo">Contas de teste</p>
        <ul>
          {CREDENCIAIS_DE_TESTE.map((credencial) => (
            <li key={credencial}>{credencial}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
