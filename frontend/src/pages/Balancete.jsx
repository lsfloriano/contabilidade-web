import { useEffect, useState } from "react";
import { getBalancete } from "../api";
import { fmt, classeValor } from "../components/graficos-comuns";

export default function Balancete() {
  const [linhas, setLinhas] = useState([]);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getBalancete()
      .then(setLinhas)
      .catch((e) => setErro(e.message));
  }, []);

  return (
    <section>
      <h2>Balancete</h2>
      {erro && <p className="erro">{erro}</p>}
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
            {linhas.map((linha) => (
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
          </tbody>
        </table>
      </div>
    </section>
  );
}
