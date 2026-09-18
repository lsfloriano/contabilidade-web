import { useState } from "react";
import Lancamentos from "./pages/Lancamentos";
import Balancete from "./pages/Balancete";
import BalancoPatrimonial from "./pages/BalancoPatrimonial";
import DRE from "./pages/DRE";
import Analise from "./pages/Analise";

const ABAS = {
  lancamentos: { rotulo: "Lançamentos", componente: Lancamentos },
  balancete: { rotulo: "Balancete", componente: Balancete },
  bp: { rotulo: "Balanço Patrimonial", componente: BalancoPatrimonial },
  dre: { rotulo: "DRE", componente: DRE },
  analise: { rotulo: "Análise", componente: Analise },
};

export default function App() {
  const [abaAtiva, setAbaAtiva] = useState("lancamentos");
  const Componente = ABAS[abaAtiva].componente;

  return (
    <div className="app">
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
