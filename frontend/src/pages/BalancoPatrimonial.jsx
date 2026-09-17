import { useEffect, useState } from "react";
import { getBP } from "../api";

function Coluna({ titulo, secoes, total }) {
  return (
    <div>
      <h3>{titulo}</h3>
      {secoes.map((secao) => (
        <div key={secao.grupo}>
          <h4>{secao.grupo}</h4>
          <table>
            <tbody>
              {secao.contas.map((conta) => (
                <tr key={conta.codigo}>
                  <td>{conta.nome}</td>
                  <td>{conta.saldo.toFixed(2)}</td>
                </tr>
              ))}
              <tr className="total-linha">
                <td>Subtotal</td>
                <td>{secao.subtotal.toFixed(2)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}
      <p className="total-linha">Total: {total.toFixed(2)}</p>
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
      {!bp.balanceado && (
        <p className="erro">
          Atenção: Ativo ({bp.total_ativo.toFixed(2)}) não bate com Passivo + PL ({bp.total_passivo_pl.toFixed(2)}).
        </p>
      )}
      <div style={{ display: "flex", gap: "32px" }}>
        <Coluna titulo="Ativo" secoes={bp.ativo} total={bp.total_ativo} />
        <Coluna titulo="Passivo + Patrimônio Líquido" secoes={bp.passivo_pl} total={bp.total_passivo_pl} />
      </div>
    </section>
  );
}
