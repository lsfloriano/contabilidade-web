import { useEffect, useState } from "react";
import { getAnalise } from "../api";
import { fmt } from "../components/graficos-comuns";

const DIRECAO_ROTULO = {
  maior_melhor: "↑ quanto maior, melhor",
  menor_melhor: "↓ quanto menor, melhor",
};

// O backend já entregou o número pronto; aqui só se escolhe a máscara.
function formatarValor(valor, formato) {
  if (formato === "percentual") return `${fmt(valor * 100)}%`;
  if (formato === "vezes") return `${fmt(valor)} vezes`;
  return fmt(valor);
}

export default function Analise() {
  const [analise, setAnalise] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getAnalise()
      .then(setAnalise)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="erro">{erro}</p>;
  if (!analise) return <p>Carregando...</p>;

  return (
    <section>
      <h2>Análise por Indicadores</h2>
      <p className="analise-intro">
        Cada indicador aparece com a fórmula, os valores substituídos e a direção
        de leitura. Não há classificação nem faixa de referência: o que é um bom
        índice depende do setor e do momento da empresa.
      </p>

      {analise.familias.map((familia) => (
        <div className="analise-familia" key={familia.nome}>
          <h3>{familia.nome}</h3>
          <table className="analise-tabela">
            <tbody>
              {familia.indicadores.map((indicador) => (
                <tr key={indicador.chave}>
                  <td>
                    <div className="analise-nome">{indicador.nome}</div>
                    <div className="analise-formula">{indicador.formula}</div>
                    <div className="analise-substituicao">
                      {fmt(indicador.numerador_valor)} / {fmt(indicador.denominador_valor)}
                    </div>
                    <div className="analise-direcao">
                      {DIRECAO_ROTULO[indicador.direcao]}
                    </div>
                    {indicador.observacao && (
                      <div className="analise-observacao">{indicador.observacao}</div>
                    )}
                  </td>
                  <td className="analise-valor">
                    {indicador.valor === null
                      ? "—"
                      : formatarValor(indicador.valor, indicador.formato)}
                    {indicador.motivo && (
                      <div
                        className={
                          indicador.nao_significativo
                            ? "analise-motivo analise-nao-significativo"
                            : "analise-motivo"
                        }
                      >
                        {indicador.motivo}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}
