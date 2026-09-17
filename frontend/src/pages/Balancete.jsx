import { useEffect, useState } from "react";
import { getBalancete } from "../api";

export default function Balancete() {
  const [linhas, setLinhas] = useState([]);

  useEffect(() => {
    getBalancete().then(setLinhas);
  }, []);

  return (
    <section>
      <h2>Balancete</h2>
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
