import { useEffect, useState } from "react";
import { getDRE } from "../api";
import GraficoDRE from "../components/GraficoDRE";

export default function DRE() {
  const [dre, setDre] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getDRE()
      .then(setDre)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!dre) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Demonstração de Resultado do Exercício</h2>

      <GraficoDRE dre={dre} />

      <h3>Receitas</h3>
      <table>
        <tbody>
          {dre.receitas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td>{conta.valor.toFixed(2)}</td>
            </tr>
          ))}
          <tr className="total-linha">
            <td>Total de receitas</td>
            <td>{dre.total_receitas.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      <h3>Despesas</h3>
      <table>
        <tbody>
          {dre.despesas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td>{conta.valor.toFixed(2)}</td>
            </tr>
          ))}
          <tr className="total-linha">
            <td>Total de despesas</td>
            <td>{dre.total_despesas.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      <p className="total-linha">
        Resultado do período: {dre.resultado_periodo.toFixed(2)}
        {dre.resultado_periodo >= 0 ? " (lucro)" : " (prejuízo)"}
      </p>
    </section>
  );
}
