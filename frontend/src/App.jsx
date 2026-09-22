import { useEffect, useState } from "react";
import Login from "./pages/Login";
import Lancamentos from "./pages/Lancamentos";
import Balancete from "./pages/Balancete";
import BalancoPatrimonial from "./pages/BalancoPatrimonial";
import DRE from "./pages/DRE";
import Dfc from "./pages/Dfc";
import Analise from "./pages/Analise";
import Comparacao from "./pages/Comparacao";
import Usuarios from "./pages/Usuarios";
import { getMe, getToken, limparToken } from "./api";

const ABAS_BASE = {
  lancamentos: { rotulo: "Lançamentos", componente: Lancamentos },
  balancete: { rotulo: "Balancete", componente: Balancete },
  bp: { rotulo: "Balanço Patrimonial", componente: BalancoPatrimonial },
  dre: { rotulo: "DRE", componente: DRE },
  dfc: { rotulo: "DFC", componente: Dfc },
  analise: { rotulo: "Análise", componente: Analise },
  comparacao: { rotulo: "Comparação", componente: Comparacao },
};

// "Usuários" é a última aba e só entra no dicionário para admin. Esconder a
// aba é conveniência, não segurança: quem forçar a chamada ainda leva 403 do
// backend.
function abasDe(usuario) {
  return usuario.papel === "admin"
    ? { ...ABAS_BASE, usuarios: { rotulo: "Usuários", componente: Usuarios } }
    : ABAS_BASE;
}

export default function App() {
  const [usuario, setUsuario] = useState(null);
  // Só existe espera se há token guardado para validar; sem token a tela de
  // login aparece na primeira pintura, sem piscar um "Carregando…".
  const [validandoToken, setValidandoToken] = useState(Boolean(getToken()));
  const [abaAtiva, setAbaAtiva] = useState("lancamentos");
  // Só existe quando getMe falha por um motivo que NÃO é sessão inválida —
  // rede fora do ar, backend inacessível etc. Nesses casos o token continua
  // guardado: o usuário não pode ser deslogado só porque o backend estava
  // fora do ar por um instante.
  const [erroDeConexao, setErroDeConexao] = useState(false);

  useEffect(() => {
    if (!getToken()) return;
    getMe()
      .then(setUsuario)
      .catch((erro) => {
        // Só a "Sessão inválida" (401 real, vindo de handleResponse/getMe)
        // derruba a sessão. Qualquer outra falha — rede, backend fora do
        // ar — é um erro de conexão, e não mexe no token guardado.
        if (erro.message === "Sessão inválida") {
          limparToken();
        } else {
          setErroDeConexao(true);
        }
      })
      .finally(() => setValidandoToken(false));
  }, []);

  function aoSair() {
    limparToken();
    setUsuario(null);
    // Volta à aba inicial: a próxima conta a entrar pode não ter acesso à
    // aba em que esta estava.
    setAbaAtiva("lancamentos");
  }

  if (validandoToken) {
    return <p className="tela-login">Carregando…</p>;
  }

  if (erroDeConexao) {
    return <p className="tela-login">Não foi possível conectar ao servidor. Tente novamente mais tarde.</p>;
  }

  if (!usuario) {
    return <Login aoEntrar={setUsuario} />;
  }

  const abas = abasDe(usuario);
  const Componente = abas[abaAtiva].componente;

  return (
    <div className="app">
      <header className="cabecalho">
        <span className="cabecalho-usuario">{usuario.nome}</span>
        <button type="button" className="botao" onClick={aoSair}>
          Sair
        </button>
      </header>
      <nav className="tabs">
        {Object.entries(abas).map(([chave, { rotulo }]) => (
          <button
            key={chave}
            className={chave === abaAtiva ? "tab tab-ativa" : "tab"}
            onClick={() => setAbaAtiva(chave)}
          >
            {rotulo}
          </button>
        ))}
      </nav>
      <main>
        <Componente />
      </main>
    </div>
  );
}
