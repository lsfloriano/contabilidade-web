import { useEffect, useState } from "react";
import { getDFC } from "../api";
import { fmt, classeValor } from "../components/graficos-comuns";

// Uma atividade: as linhas de conta mais o subtotal. Mesma estrutura de
// tabela + `.razao-subtotal` das seções de Receitas/Despesas da DRE. Sem
// linhas (atividade sem movimento no período), sobra o subtotal zerado — a
// seção continua visível, que é o que permite ler a demonstração inteira sem
// se perguntar se uma atividade sumiu ou não teve movimento.
function Atividade({ titulo, linhas, rotuloSubtotal, subtotal }) {
  return (
    <>
      <h3>{titulo}</h3>
      <table>
        <tbody>
          {linhas.map((linha) => (
            <tr key={linha.codigo}>
              <td>{linha.nome}</td>
              <td className={classeValor(linha.valor)}>{fmt(linha.valor)}</td>
            </tr>
          ))}
          <tr className="razao-subtotal">
            <td>{rotuloSubtotal}</td>
            <td className={classeValor(subtotal)}>{fmt(subtotal)}</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

export default function Dfc() {
  const [dfc, setDfc] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getDFC()
      .then(setDfc)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!dfc) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Demonstração de Fluxo de Caixa</h2>
      {/* Por construção esta igualdade nunca falha — excluir os lançamentos
          entre Caixa e Bancos não muda a soma Caixa+Bancos. O aviso é a mesma
          rede de segurança que o `!bp.balanceado` do Balanço Patrimonial. */}
      {!dfc.confere && (
        <p className="erro">
          Atenção: o saldo final de caixa ({fmt(dfc.saldo_final)}) não bate com
          o saldo de Caixa + Bancos do balancete.
        </p>
      )}

      <Atividade
        titulo="Atividades operacionais"
        linhas={dfc.operacionais}
        rotuloSubtotal="Caixa líquido das atividades operacionais"
        subtotal={dfc.subtotal_operacionais}
      />
      <Atividade
        titulo="Atividades de investimento"
        linhas={dfc.investimentos}
        rotuloSubtotal="Caixa líquido das atividades de investimento"
        subtotal={dfc.subtotal_investimentos}
      />
      <Atividade
        titulo="Atividades de financiamento"
        linhas={dfc.financiamentos}
        rotuloSubtotal="Caixa líquido das atividades de financiamento"
        subtotal={dfc.subtotal_financiamentos}
      />

      <h3>Fechamento de caixa</h3>
      <table>
        <tbody>
          <tr>
            <td>Saldo inicial de caixa</td>
            <td className={classeValor(dfc.saldo_inicial)}>
              {fmt(dfc.saldo_inicial)}
            </td>
          </tr>
          <tr className="razao-subtotal">
            <td>Variação líquida de caixa</td>
            <td className={classeValor(dfc.variacao_liquida)}>
              {fmt(dfc.variacao_liquida)}
            </td>
          </tr>
        </tbody>
      </table>
      <p className="razao-fechamento">
        <span>Saldo final de caixa</span>
        <span className={classeValor(dfc.saldo_final)}>
          {fmt(dfc.saldo_final)}
        </span>
      </p>
    </section>
  );
}
