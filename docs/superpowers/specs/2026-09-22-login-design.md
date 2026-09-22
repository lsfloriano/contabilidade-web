# Login — design

## Objetivo

Sistema de autenticação simples: três contas fixas (uma admin, duas comuns),
token JWT, e proteção de todas as rotas existentes. Fundação para uma futura
expansão multi-empresa (plano de contas por empresa) — **não** implementada
agora, deliberadamente.

## Fora de escopo (decisão explícita do usuário)

- **Plano de contas por empresa.** É o motivo original que trouxe este
  pedido, mas é um trabalho muito maior — exige um conceito de "empresa" no
  banco, CRUD de plano de contas (que não existe hoje: `/contas` é só
  leitura), e todo relatório (Balancete, BP, DRE, DFC, Análise, Comparação)
  escopado por empresa. Fica para um próximo brainstorming, separado.
- **Cadastro público de usuário.** As três contas são semeadas no backend,
  como o plano de contas já é. Não existe tela de "criar conta".
- **Recuperação de senha.** Sem e-mail, sem "esqueci minha senha" — é
  ambiente de demonstração.
- **Refresh token.** O token expira em 24h e o usuário loga de novo; sem
  renovação automática.

## Mecanismo: JWT, não cookie de sessão

Login devolve um token; o frontend guarda no `localStorage` e manda em
`Authorization: Bearer <token>` em toda chamada. Evita configurar cookie
cross-origin (a API já roda em porta diferente do frontend, 8000 vs 5173) —
sem `credentials: 'include'`, sem `SameSite`, sem `allow_credentials` no CORS.

Bibliotecas novas (legítimas — a feature genuinamente precisa delas, ao
contrário do resto do projeto, que evitou dependências novas por não
precisar): `bcrypt==4.2.1` (hash de senha) e `PyJWT==2.10.1` (token).

## Modelo de dados

Tabela nova, `Usuario`: `id`, `email` (único), `nome`, `senha_hash`, `papel`
(`admin` ou `comum`). Nenhuma tabela existente muda.

## Backend

- `backend/app/auth.py` (novo): `hash_senha`/`verificar_senha` (bcrypt),
  `criar_token`/`decodificar_token` (JWT, expiração 24h), e duas dependencies
  do FastAPI: `usuario_atual` (decodifica o header `Authorization`, 401 se
  ausente/inválido/expirado) e `exigir_admin` (chama `usuario_atual` e checa
  `papel == "admin"`, 403 caso contrário).

  O payload do token carrega só `sub` (o e-mail) e `exp` (expiração) — não o
  `papel`. `usuario_atual` busca o usuário no banco pelo e-mail do `sub` e
  devolve o registro atual, papel incluído. Isso é deliberado: se o papel de
  alguém mudasse (uma conta comum virasse admin, por exemplo) enquanto o
  token velho ainda estivesse válido, confiar num `papel` gravado no token na
  hora do login deixaria essa mudança sem efeito até o token expirar. Buscar
  de novo no banco a cada requisição custa uma consulta simples e evita essa
  janela.
- `POST /login` — recebe `{email, senha}`, devolve `{token, nome, papel}`.
  401 se credencial errada.
- `GET /me` — protegida, devolve `{email, nome, papel}` do token atual. É o
  que o frontend chama ao carregar a página com um token salvo, para
  confirmar que ainda vale sem obrigar login de novo.
- `GET /usuarios` e `POST /usuarios` — só admin (`Depends(exigir_admin)`).
  Criar usuário recebe `{email, nome, senha, papel}`.
- **Todas as rotas que já existem** (`/contas`, `/lancamentos` e suas
  variantes, `/relatorios/*`) ganham `Depends(usuario_atual)`. `POST /login`
  é a única rota aberta, além do health-check `GET /`.
- Seed de três usuários, no mesmo `lifespan` que já semeia o plano de contas:
  - `admin@contabilidade.com` / `admin123` — papel `admin`
  - `teste1@contabilidade.com` / `teste123` — papel `comum`
  - `teste2@contabilidade.com` / `teste123` — papel `comum`

## Frontend

- `Login.jsx` (novo): formulário e-mail/senha reaproveitando `.campo`/
  `.campo-rotulo`/`.botao`/`.erro` já existentes. Um aviso abaixo do
  formulário mostra as três credenciais de teste — decisão deliberada do
  usuário: é ambiente de demonstração, e isso deixa qualquer pessoa avaliando
  o projeto entrar sozinha.
- `App.jsx`: novo estado `usuario` (`null` = não logado). Ao carregar, se
  houver token no `localStorage`, chama `GET /me`; se falhar, limpa o token e
  mostra login. Com `usuario` preenchido, mostra o app de sempre, com um
  cabeçalho novo (nome do usuário + botão "Sair") acima da faixa de abas.
  Aba "Usuários" só entra no dicionário `ABAS` quando `usuario.papel ===
  "admin"`. A aba ativa inicial continua sendo `lancamentos`, como hoje —
  login não muda qual aba abre primeiro, só o que precisa acontecer antes de
  qualquer aba aparecer.
- `Usuarios.jsx` (novo, só alcançável por admin): lista de usuários e um
  formulário de criar (mesmos componentes de formulário do resto do app).
- `api.js`: `login(email, senha)`, `getMe()`, `getUsuarios()`,
  `criarUsuario(dados)`. Toda função exportada existente (`getContas`,
  `getLancamentos`, `criarLancamento`, `estornarLancamento`,
  `uploadLancamentos`, `getBalancete`, `getBP`, `getDRE`, `getDFC`,
  `getAnalise`, as três `*_planilha`) passa a mandar
  `Authorization: Bearer <token>`. Um `handleResponse` que recebe `401`
  limpa o `localStorage` e recarrega a página, jogando de volta pro login —
  sem isso, um token expirado no meio do uso vira uma tela de erro confusa em
  vez de simplesmente pedir login de novo.
- CSS — o bloco inteiro que este trabalho acrescenta, literal, para não
  deixar a decisão de layout em aberto:

```css
/* Tela de login: ocupa a viewport inteira, sem fio nem caixa ao redor do
   formulário — um cartão de login quebraria a regra do resto do app ("fio,
   não caixa"; nenhuma tabela ou formulário vive dentro de uma caixa em
   nenhuma outra página). Título e formulário centralizados; a largura do
   formulário é contida para não esticar numa tela larga. */
.tela-login {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px;
  box-sizing: border-box;
}

/* Reaproveita a grade de .form-lancamento, só com uma coluna e largura
   menor: o formulário de login tem dois campos empilhados, não três lado a
   lado como o de lançar. */
.tela-login .form-lancamento {
  width: 100%;
  max-width: 360px;
  grid-template-columns: 1fr;
}
```

  Nenhum outro CSS novo — o restante da tela de login (campos, rótulos,
  botão, mensagem de erro) usa exatamente `.campo`/`.campo-rotulo`/`.botao`/
  `.erro` como já existem.

## Testes

Backend (pytest):

- Login com credencial certa devolve token; com credencial errada, 401.
- `GET /me` com token válido devolve os dados certos; sem token, 401; com
  token malformado, 401.
- Uma rota já existente (ex.: `GET /lancamentos`) sem token devolve 401; com
  token de qualquer papel, 200.
- `GET /usuarios`/`POST /usuarios` com token de conta `comum` devolve 403;
  com token de conta `admin`, funciona.
- Token expirado é rejeitado (testável construindo um token com expiração no
  passado diretamente via `criar_token`/`jwt.encode`, sem esperar 24h de
  verdade).

Frontend: sem framework de teste, convenção já estabelecida do projeto.
Verificação visual pelo coordenador, no navegador — login com as três
contas, tentativa de acessar "Usuários" como conta comum, token expirado
simulado (apagar do localStorage manualmente) devolvendo à tela de login.

## Arquivos afetados

- `backend/app/models.py` — `Usuario` (modificar)
- `backend/app/auth.py` (criar)
- `backend/app/schemas.py` — schemas de login/usuário (modificar)
- `backend/app/routers/auth.py` (criar) — `/login`, `/me`
- `backend/app/routers/usuarios.py` (criar) — `/usuarios`
- `backend/app/routers/contas.py`, `lancamentos.py`, `relatorios.py` —
  `Depends(usuario_atual)` em cada rota (modificar)
- `backend/app/seed.py` — seed de usuários (modificar)
- `backend/app/main.py` — registra routers novos, chama seed novo (modificar)
- `backend/requirements.txt` — `bcrypt`, `PyJWT` (modificar)
- `backend/tests/test_auth.py` (criar)
- `frontend/src/pages/Login.jsx` (criar)
- `frontend/src/pages/Usuarios.jsx` (criar)
- `frontend/src/api.js` — funções novas + header em todas as existentes
  (modificar)
- `frontend/src/App.jsx` — estado de usuário, cabeçalho, aba condicional
  (modificar)
- `frontend/src/index.css` — uma classe de centralização para a tela de
  login (modificar)
