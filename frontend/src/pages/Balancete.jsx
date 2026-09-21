import { useEffect, useState } from "react";
import { getBalancete } from "../api";
import { fmt, classeValor } from "../components/graficos-comuns";

export default function Balancete() {
  const [balancete, setBalancete] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getBalancete()
      .then(setBalancete)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!balancete) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Balancete</h2>
      <div className="tabela-rolagem">
        <table>
          <thead>
            <tr>
              <th>Conta</th>
              <th>Grupo</th>
              <th className="razao-valor">Total débito</th>
              <th className="razao-valor">Total crédito</th>
              <th className="razao-valor">Saldo</th>
            </tr>
          </thead>
          <tbody>
            {balancete.linhas.map((linha) => (
              <tr key={linha.codigo}>
                <td>
                  {linha.codigo} - {linha.nome}
                </td>
                <td>{linha.grupo}</td>
                <td className={classeValor(linha.total_debito)}>
                  {fmt(linha.total_debito)}
                </td>
                <td className={classeValor(linha.total_credito)}>
                  {fmt(linha.total_credito)}
                </td>
                <td className={classeValor(linha.saldo)}>{fmt(linha.saldo)}</td>
              </tr>
            ))}
            <tr className="razao-subtotal razao-total-tabela">
              <td colSpan={2}>Total</td>
              <td className={classeValor(balancete.total_debito)}>
                {fmt(balancete.total_debito)}
              </td>
              <td className={classeValor(balancete.total_credito)}>
                {fmt(balancete.total_credito)}
              </td>
              <td
                className={classeValor(
                  balancete.total_debito - balancete.total_credito
                )}
              >
                {fmt(balancete.total_debito - balancete.total_credito)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
