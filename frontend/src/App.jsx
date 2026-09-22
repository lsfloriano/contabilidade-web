import { useEffect, useState } from "react";
import Login from "./pages/Login";
import Lancamentos from "./pages/Lancamentos";
import Balancete from "./pages/Balancete";
import BalancoPatrimonial from "./pages/BalancoPatrimonial";
import DRE from "./pages/DRE";
import Dfc from "./pages/Dfc";
import Analise from "./pages/Analise";
import Comparacao from "./pages/Comparacao";
import { getMe, getToken, limparToken } from "./api";

const ABAS = {
  lancamentos: { rotulo: "Lançamentos", componente: Lancamentos },
  balancete: { rotulo: "Balancete", componente: Balancete },
  bp: { rotulo: "Balanço Patrimonial", componente: BalancoPatrimonial },
  dre: { rotulo: "DRE", componente: DRE },
  dfc: { rotulo: "DFC", componente: Dfc },
  analise: { rotulo: "Análise", componente: Analise },
  comparacao: { rotulo: "Comparação", componente: Comparacao },
};

export default function App() {
  const [usuario, setUsuario] = useState(null);
  // Só existe espera se há token guardado para validar; sem token a tela de
  // login aparece na primeira pintura, sem piscar um "Carregando…".
  const [validandoToken, setValidandoToken] = useState(Boolean(getToken()));
  const [abaAtiva, setAbaAtiva] = useState("lancamentos");

  useEffect(() => {
    if (!getToken()) return;
    getMe()
      .then(setUsuario)
      .catch(() => limparToken())
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

  if (!usuario) {
    return <Login aoEntrar={setUsuario} />;
  }

  const Componente = ABAS[abaAtiva].componente;

  return (
    <div className="app">
      <header className="cabecalho">
        <span className="cabecalho-usuario">{usuario.nome}</span>
        <button type="button" className="botao" onClick={aoSair}>
          Sair
        </button>
      </header>
      <nav className="tabs">
        {Object.entries(ABAS).map(([chave, { rotulo }]) => (
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
