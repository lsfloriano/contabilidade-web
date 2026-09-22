import { useEffect, useState } from "react";
import { getDRE, getDREPlanilha, salvarArquivo } from "../api";
import GraficoDRE from "../components/GraficoDRE";
import { fmt, classeValor, arredondar } from "../components/graficos-comuns";

export default function DRE() {
  const [dre, setDre] = useState(null);
  const [erro, setErro] = useState(null);
  const [erroExportar, setErroExportar] = useState(null);

  useEffect(() => {
    getDRE()
      .then(setDre)
      .catch((e) => setErro(e.message));
  }, []);

  async function aoExportar() {
    setErroExportar(null);
    try {
      salvarArquivo(await getDREPlanilha(), "dre.xlsx");
    } catch (e) {
      setErroExportar(e.message);
    }
  }

  if (erro) return <p className="erro">{erro}</p>;
  if (!dre) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Demonstração de Resultado do Exercício</h2>
      <button type="button" className="botao" onClick={aoExportar}>
        Exportar
      </button>
      {erroExportar && <p className="erro">{erroExportar}</p>}

      <GraficoDRE dre={dre} />

      <h3>Receitas</h3>
      <table>
        <tbody>
          {dre.receitas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td className={classeValor(conta.valor)}>{fmt(conta.valor)}</td>
            </tr>
          ))}
          <tr className="razao-subtotal">
            <td>Total de receitas</td>
            <td className={classeValor(dre.total_receitas)}>
              {fmt(dre.total_receitas)}
            </td>
          </tr>
        </tbody>
      </table>

      <h3>Despesas</h3>
      <table>
        <tbody>
          {dre.despesas.map((conta) => (
            <tr key={conta.codigo}>
              <td>{conta.nome}</td>
              <td className={classeValor(conta.valor)}>{fmt(conta.valor)}</td>
            </tr>
          ))}
          <tr className="razao-subtotal">
            <td>Total de despesas</td>
            <td className={classeValor(dre.total_despesas)}>
              {fmt(dre.total_despesas)}
            </td>
          </tr>
        </tbody>
      </table>

      <p className="razao-fechamento">
        <span>
          Resultado do período
          {arredondar(dre.resultado_periodo) >= 0 ? " (lucro)" : " (prejuízo)"}
        </span>
        <span className={classeValor(dre.resultado_periodo)}>
          {fmt(dre.resultado_periodo)}
        </span>
      </p>
    </section>
  );
}
