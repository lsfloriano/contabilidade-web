import { useEffect, useState } from "react";
import { getBP } from "../api";
import GraficoBalanco from "../components/GraficoBalanco";
import { fmt, classeValor } from "../components/graficos-comuns";

function Coluna({ titulo, secoes, total }) {
  return (
    <div className="bp-coluna">
      <h3>{titulo}</h3>
      {secoes.map((secao) => (
        <div key={secao.grupo}>
          <h4>{secao.grupo}</h4>
          <table>
            <tbody>
              {secao.contas.map((conta) => (
                <tr key={conta.codigo}>
                  <td>{conta.nome}</td>
                  <td className={classeValor(conta.saldo)}>
                    {fmt(conta.saldo)}
                  </td>
                </tr>
              ))}
              <tr className="razao-subtotal">
                <td>Subtotal</td>
                <td className={classeValor(secao.subtotal)}>
                  {fmt(secao.subtotal)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}
      <p className="razao-fechamento">
        <span>Total</span>
        <span className={classeValor(total)}>{fmt(total)}</span>
      </p>
    </div>
  );
}

export default function BalancoPatrimonial() {
  const [bp, setBp] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getBP()
      .then(setBp)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!bp) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Balanço Patrimonial</h2>
      <a href="http://localhost:8000/relatorios/bp/exportar" className="botao" download>
        Exportar
      </a>
      {!bp.balanceado && (
        <p className="erro">
          Atenção: Ativo ({fmt(bp.total_ativo)}) não bate com Passivo + PL (
          {fmt(bp.total_passivo_pl)}).
        </p>
      )}
      <GraficoBalanco bp={bp} />
      <div className="bp-colunas">
        <Coluna titulo="Ativo" secoes={bp.ativo} total={bp.total_ativo} />
        <Coluna
          titulo="Passivo + Patrimônio Líquido"
          secoes={bp.passivo_pl}
          total={bp.total_passivo_pl}
        />
      </div>
    </section>
  );
}
