import { useState } from "react";
import { getBP, getDRE } from "../api";
import { fmt, classeValor, arredondar, formatarData } from "../components/graficos-comuns";

const PERIODO_VAZIO = { inicio: "", fim: "" };

// Variação percentual entre dois instantes da MESMA grandeza — aritmética de
// exibição, da mesma família de `fmt` e `classeValor`, não cálculo contábil.
//
// Devolve null quando a base é zero: a divisão não existe e a página mostra
// "—", nunca Infinity nem NaN. Os dois operandos passam por `arredondar` ANTES
// da divisão porque o backend soma floats crus: uma base de resíduo (1e-9)
// produziria bilhões de por cento em vez de "—". O resultado passa por
// `arredondar` de novo porque Math.round devolve -0 para quedas ínfimas, e
// "-0,00%" em vermelho é o bug de sinal que este projeto já corrigiu duas
// vezes. Divide por Math.abs(base), não por base: com base negativa é isso que
// preserva o sentido de melhora/piora (−1000 -> −500 dá +50%).
function variacaoPercentual(valor1, valor2) {
  const base = arredondar(valor1);
  if (base === 0) return null;
  return arredondar(((arredondar(valor2) - base) / Math.abs(base)) * 100);
}

function textoVariacao(percentual) {
  if (percentual === null) return "—";
  return `${percentual > 0 ? "+" : ""}${fmt(percentual)}%`;
}

function classeVariacao(percentual) {
  return percentual === null ? "razao-valor" : classeValor(percentual);
}

function TabelaComparacao({ linhas, tituloConta = "Conta" }) {
  return (
    <table>
      <thead>
        <tr>
          <th className="comparacao-conta">{tituloConta}</th>
          <th className="razao-valor">Período 1</th>
          <th className="razao-valor">Período 2</th>
          <th className="razao-valor">Variação</th>
        </tr>
      </thead>
      <tbody>
        {linhas.map((linha) => {
          const percentual = variacaoPercentual(linha.valor1, linha.valor2);
          return (
            <tr key={linha.chave} className={linha.className}>
              <td>{linha.rotulo}</td>
              <td className={classeValor(linha.valor1)}>{fmt(linha.valor1)}</td>
              <td className={classeValor(linha.valor2)}>{fmt(linha.valor2)}</td>
              <td className={classeVariacao(percentual)}>{textoVariacao(percentual)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// Pareia por índice, não por código: calcular_balancete percorre o plano de
// contas inteiro com filtro ou sem ele, então os dois períodos têm sempre as
// mesmas seções e as mesmas contas, na mesma ordem — conta sem movimento no
// recorte vem com saldo 0, não some.
function linhasDasSecoes(secoes1, secoes2) {
  const linhas = [];
  secoes1.forEach((secao1, i) => {
    const secao2 = secoes2[i];
    secao1.contas.forEach((conta1, j) => {
      linhas.push({
        chave: `${secao1.grupo}-${conta1.codigo}`,
        rotulo: conta1.nome,
        valor1: conta1.saldo,
        valor2: secao2.contas[j]?.saldo ?? 0,
      });
    });
    linhas.push({
      chave: `${secao1.grupo}-subtotal`,
      rotulo: `Subtotal — ${secao1.grupo}`,
      valor1: secao1.subtotal,
      valor2: secao2.subtotal,
      className: "razao-subtotal",
    });
  });
  return linhas;
}

function linhasDasContas(contas1, contas2, prefixo) {
  return contas1.map((conta1, i) => ({
    chave: `${prefixo}-${conta1.codigo}`,
    rotulo: conta1.nome,
    valor1: conta1.valor,
    valor2: contas2[i]?.valor ?? 0,
  }));
}

function linhaTotal(chave, rotulo, valor1, valor2) {
  return {
    chave,
    rotulo,
    valor1,
    valor2,
    className: "razao-subtotal razao-total-tabela",
  };
}

export default function Comparacao() {
  const [periodo1, setPeriodo1] = useState(PERIODO_VAZIO);
  const [periodo2, setPeriodo2] = useState(PERIODO_VAZIO);
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);

  // Datas ISO (AAAA-MM-DD) comparam certo como string: os campos são de
  // largura fixa e vão do mais significativo ao menos.
  const invertido1 = periodo1.inicio !== "" && periodo1.fim !== "" && periodo1.inicio > periodo1.fim;
  const invertido2 = periodo2.inicio !== "" && periodo2.fim !== "" && periodo2.inicio > periodo2.fim;

  async function aoComparar(evento) {
    evento.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      const [bp1, bp2, dre1, dre2] = await Promise.all([
        getBP(periodo1.fim),
        getBP(periodo2.fim),
        getDRE(periodo1.inicio, periodo1.fim),
        getDRE(periodo2.inicio, periodo2.fim),
      ]);
      // Guarda os períodos junto com os dados: as legendas têm de mostrar o
      // que foi consultado, não o que o usuário digitou depois.
      setDados({ bp1, bp2, dre1, dre2, p1: periodo1, p2: periodo2 });
    } catch (e) {
      setErro(e.message);
      setDados(null);
    }
    setCarregando(false);
  }

  return (
    <section>
      <h2>Comparação entre períodos</h2>
      <p className="comparacao-intro">
        O Balanço Patrimonial é uma foto: acumula tudo desde o primeiro
        lançamento até a data de fim do período. A DRE é fluxo: só o que ocorreu
        dentro do intervalo. Por isso a data de fim alimenta os dois relatórios
        e a data de início alimenta só a DRE.
      </p>

      <form className="comparacao-form" onSubmit={aoComparar}>
        <label className="campo">
          <span className="campo-rotulo">Período 1 — início</span>
          <input
            type="date"
            value={periodo1.inicio}
            onChange={(e) => setPeriodo1({ ...periodo1, inicio: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Período 1 — fim</span>
          <input
            type="date"
            value={periodo1.fim}
            onChange={(e) => setPeriodo1({ ...periodo1, fim: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Período 2 — início</span>
          <input
            type="date"
            value={periodo2.inicio}
            onChange={(e) => setPeriodo2({ ...periodo2, inicio: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span className="campo-rotulo">Período 2 — fim</span>
          <input
            type="date"
            value={periodo2.fim}
            onChange={(e) => setPeriodo2({ ...periodo2, fim: e.target.value })}
            required
          />
        </label>
        <button type="submit" className="botao">
          Comparar
        </button>
      </form>

      {invertido1 && (
        <p className="comparacao-aviso">
          Aviso: no Período 1 a data de início é posterior à de fim. O intervalo
          não contém nenhum lançamento e a DRE sairá zerada.
        </p>
      )}
      {invertido2 && (
        <p className="comparacao-aviso">
          Aviso: no Período 2 a data de início é posterior à de fim. O intervalo
          não contém nenhum lançamento e a DRE sairá zerada.
        </p>
      )}
      {erro && <p className="erro">{erro}</p>}
      {carregando && <p>Carregando...</p>}
      {!carregando && !dados && !erro && (
        <p className="comparacao-vazio">
          Escolha os dois períodos e clique em Comparar.
        </p>
      )}

      {!carregando && dados && (
        <>
          <h3>Balanço Patrimonial</h3>
          <p className="comparacao-legenda">
            Foto acumulada até {formatarData(dados.p1.fim)} (Período 1) e até{" "}
            {formatarData(dados.p2.fim)} (Período 2). A linha "Resultado do
            Exercício (não realizado)" acumula desde o primeiro lançamento até
            a data de fim de cada período, enquanto a DRE abaixo mostra só o
            que ocorreu dentro do intervalo — por isso os dois "Resultado"
            podem divergir, e isso não é um erro.
          </p>
          {!dados.bp1.balanceado && (
            <p className="erro">
              Atenção: no Período 1 o Ativo ({fmt(dados.bp1.total_ativo)}) não
              bate com Passivo + PL ({fmt(dados.bp1.total_passivo_pl)}).
            </p>
          )}
          {!dados.bp2.balanceado && (
            <p className="erro">
              Atenção: no Período 2 o Ativo ({fmt(dados.bp2.total_ativo)}) não
              bate com Passivo + PL ({fmt(dados.bp2.total_passivo_pl)}).
            </p>
          )}

          <h4>Ativo</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasSecoes(dados.bp1.ativo, dados.bp2.ativo),
                linhaTotal(
                  "total-ativo",
                  "Total do Ativo",
                  dados.bp1.total_ativo,
                  dados.bp2.total_ativo
                ),
              ]}
            />
          </div>

          <h4>Passivo + Patrimônio Líquido</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasSecoes(dados.bp1.passivo_pl, dados.bp2.passivo_pl),
                linhaTotal(
                  "total-passivo-pl",
                  "Total do Passivo + PL",
                  dados.bp1.total_passivo_pl,
                  dados.bp2.total_passivo_pl
                ),
              ]}
            />
          </div>

          <h3>Demonstração de Resultado do Exercício</h3>
          <p className="comparacao-legenda">
            Fluxo de {formatarData(dados.p1.inicio)} a {formatarData(dados.p1.fim)}{" "}
            (Período 1) e de {formatarData(dados.p2.inicio)} a{" "}
            {formatarData(dados.p2.fim)} (Período 2).
          </p>

          <h4>Receitas</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasContas(dados.dre1.receitas, dados.dre2.receitas, "receita"),
                linhaTotal(
                  "total-receitas",
                  "Total de receitas",
                  dados.dre1.total_receitas,
                  dados.dre2.total_receitas
                ),
              ]}
            />
          </div>

          <h4>Despesas</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              linhas={[
                ...linhasDasContas(dados.dre1.despesas, dados.dre2.despesas, "despesa"),
                linhaTotal(
                  "total-despesas",
                  "Total de despesas",
                  dados.dre1.total_despesas,
                  dados.dre2.total_despesas
                ),
              ]}
            />
          </div>

          <h4>Resultado</h4>
          <div className="tabela-rolagem">
            <TabelaComparacao
              tituloConta=""
              linhas={[
                linhaTotal(
                  "resultado-periodo",
                  "Resultado do período",
                  dados.dre1.resultado_periodo,
                  dados.dre2.resultado_periodo
                ),
              ]}
            />
          </div>
        </>
      )}
    </section>
  );
}
