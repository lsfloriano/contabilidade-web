import { useEffect, useState } from "react";
import { getBalancete } from "../api";

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
      <table>
        <thead>
          <tr>
            <th>Conta</th>
            <th>Grupo</th>
            <th>Total débito</th>
            <th>Total crédito</th>
            <th>Saldo</th>
          </tr>
        </thead>
        <tbody>
          {linhas.map((linha) => (
            <tr key={linha.codigo}>
              <td>{linha.codigo} - {linha.nome}</td>
              <td>{linha.grupo}</td>
              <td>{linha.total_debito.toFixed(2)}</td>
              <td>{linha.total_credito.toFixed(2)}</td>
              <td>{linha.saldo.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
