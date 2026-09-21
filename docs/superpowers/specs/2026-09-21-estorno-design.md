# Estorno de lançamentos — design

## Objetivo

Hoje o app só lança — não existe como corrigir um erro sem mexer direto no
banco. Na contabilidade real nunca se apaga um lançamento errado, se estorna:
um lançamento reverso (débito e crédito trocados, mesmo valor), referenciando
o original. Este trabalho adiciona essa mecânica.

## Fora de escopo

- **Editar ou excluir um lançamento existente.** Continua não existindo, de
  propósito — é o mesmo motivo pelo qual o estorno existe: a contabilidade não
  apaga, corrige com um lançamento novo.
- **Restringir quantas vezes um lançamento pode ser estornado.** O app não
  valida lançamento duplicado hoje (dá pra lançar a mesma coisa duas vezes por
  engano); adicionar essa validação só para o estorno seria inconsistente com
  o resto do app.
- **Migração de banco de dados.** `init_db` só roda `create_all`, que não
  altera tabela existente — nunca houve migração neste projeto. A coluna nova
  (`estorno_de`) exige apagar e recriar o `contabilidade.db` de
  desenvolvimento local; não vamos escrever um mecanismo de `ALTER TABLE`
  condicional para isso.

## Modelo de dados

Uma coluna nova em `Lancamento`: `estorno_de: int | None`, FK nullable para
`Lancamento.id` — presente **só** no lançamento que é o estorno, apontando
para o original. O original não ganha nenhuma coluna nova; se ele foi
estornado, isso se deriva olhando se algum outro lançamento tem `estorno_de`
apontando para ele. Uma flag redundante no original (`estornado: bool`)
duplicaria essa informação sem necessidade.

## Por que nenhum relatório muda

Um estorno é só mais um lançamento normal, com débito e crédito invertidos.
`calcular_balancete` (e por extensão Balancete, BP, DRE, DFC) já cancela o
original automaticamente pela própria aritmética da partida dobrada — a soma
de dois lançamentos com os mesmos valores e os mesmos dois lados, um em cada
direção, é zero, sem nenhum código novo saber que "estorno" existe.
`backend/app/relatorios.py` não é tocado por este trabalho.

## Endpoint

`POST /lancamentos/{id}/estorno`, corpo `{ "data": date, "historico":
string | null }`. O backend busca o lançamento original pelo `id` (404 se não
existir), monta o novo lançamento com `conta_debito`/`conta_credito`
invertidos e o mesmo `valor` do original, e `estorno_de = id`. Se
`historico` vier vazio, o backend gera um padrão: `"Estorno do lançamento
#{id}: {histórico original}"` (ou só `"Estorno do lançamento #{id}"` se o
original não tinha histórico). Passa pela mesma `validar_lancamento` que
`POST /lancamentos` já usa — redundante na prática (débito/crédito invertidos
de um lançamento válido são sempre válidos), mas sem custo e consistente.

`GET /lancamentos` passa a devolver `estorno_de` em cada lançamento
(`null` quando não é um estorno) — é a única mudança na leitura, e é o que o
frontend usa para derivar as duas indicações visuais abaixo, sem endpoint
novo para isso.

## Frontend

**Botão "Estornar" em cada linha** da tabela "Lançamentos existentes", em
toda linha, sem exceção (nenhum lançamento fica proibido de ser estornado,
inclusive um estorno já existente ou um lançamento já estornado — consistente
com "sem restrição de quantas vezes").

**Ao clicar**, o formulário do topo da página (o mesmo já usado para lançar)
se preenche com `conta_debito`/`conta_credito` **invertidos** e o mesmo
`valor` da linha clicada — e esses três campos ficam **desabilitados**: um
estorno é por definição o reverso exato do original, então não faz sentido
deixar editar. Só **data** (em branco, o usuário preenche) e **histórico**
(pré-preenchido com o padrão que o backend geraria, editável) ficam livres.
O botão de submeter muda de rótulo, de "Lançar" para "Confirmar estorno",
e chama `POST /lancamentos/{id}/estorno` em vez de `POST /lancamentos`
enquanto o formulário estiver em "modo estorno" (os três campos travados). Um
botão "Cancelar" aparece ao lado só nesse modo, destravando os campos e
limpando o formulário sem enviar nada. Confirmar o estorno também volta o
formulário ao modo normal (campos livres, todos vazios), do mesmo jeito que
lançar um lançamento comum já limpa o formulário hoje.

**Indicação visual na tabela**, derivada no frontend a partir dos dados que
`GET /lancamentos` já traz, sem cálculo novo:

- Uma linha que é um estorno mostra, junto do histórico, `"(estorno do
  lançamento #N)"`.
- Uma linha que foi estornada por outro lançamento mostra `"(estornado pelo
  lançamento #M)"`.

## Testes

Backend (pytest, padrão de `backend/tests/`):

- `POST /lancamentos/{id}/estorno` cria um lançamento com débito/crédito
  invertidos, mesmo valor, `estorno_de` correto.
- Histórico padrão gerado quando não fornecido; histórico customizado
  respeitado quando fornecido.
- 404 ao estornar um `id` inexistente.
- `GET /lancamentos` devolve `estorno_de` corretamente (`null` para
  lançamentos normais, o `id` do original para um estorno).
- Um teste de fechamento: lançar, estornar, e confirmar que
  `calcular_balancete` (ou `montar_balancete`) volta a zero para as contas
  envolvidas — a prova de que o estorno cancela o original pela própria
  aritmética, sem nenhum código de relatório saber disso.

Frontend: sem framework de teste, convenção já estabelecida do projeto.
Verificação visual pelo coordenador, no navegador.

## Arquivos afetados

- `backend/app/models.py` — coluna `estorno_de` em `Lancamento` (modificar)
- `backend/app/schemas.py` — `estorno_de` em `LancamentoOut`,
  `LancamentoEstornoCreate` novo (modificar)
- `backend/app/routers/lancamentos.py` — rota `POST
  /lancamentos/{id}/estorno` (modificar)
- `backend/tests/test_lancamentos_api.py` — testes novos (modificar)
- `frontend/src/pages/Lancamentos.jsx` — botão, modo estorno do formulário,
  indicações visuais (modificar)
- `frontend/src/api.js` — `estornarLancamento(id, dados)` (modificar)

Antes de rodar: apagar `backend/contabilidade.db` (ambiente de
desenvolvimento local) para a coluna nova ser criada do zero.
