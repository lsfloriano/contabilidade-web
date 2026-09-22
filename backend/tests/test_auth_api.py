from app.auth import criar_token


def test_login_com_credencial_certa_devolve_token_nome_e_papel(client_sem_token):
    resposta = client_sem_token.post(
        "/login",
        json={"email": "admin@contabilidade.com", "senha": "admin123"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token"]
    assert corpo["nome"] == "Administrador"
    assert corpo["papel"] == "admin"


def test_login_de_conta_comum_devolve_papel_comum(client_sem_token):
    resposta = client_sem_token.post(
        "/login",
        json={"email": "teste1@contabilidade.com", "senha": "teste123"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["papel"] == "comum"


def test_login_com_email_em_caixa_diferente_funciona(client_sem_token):
    resposta = client_sem_token.post(
        "/login",
        json={"email": "Admin@Contabilidade.com", "senha": "admin123"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["papel"] == "admin"


def test_login_com_senha_errada_devolve_401(client_sem_token):
    resposta = client_sem_token.post(
        "/login",
        json={"email": "admin@contabilidade.com", "senha": "senha-errada"},
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha inválidos"


def test_login_com_email_inexistente_devolve_401(client_sem_token):
    resposta = client_sem_token.post(
        "/login",
        json={"email": "ninguem@contabilidade.com", "senha": "teste123"},
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha inválidos"


def test_me_com_token_valido_devolve_os_dados_do_usuario(client):
    resposta = client.get("/me")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "email": "teste1@contabilidade.com",
        "nome": "Usuário Teste 1",
        "papel": "comum",
    }


def test_me_sem_token_devolve_401(client_sem_token):
    resposta = client_sem_token.get("/me")

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Não autenticado"


def test_me_com_token_malformado_devolve_401(client_sem_token):
    resposta = client_sem_token.get("/me", headers={"Authorization": "Bearer nao-e-token"})

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Token inválido ou expirado"


def test_me_com_header_sem_prefixo_bearer_devolve_401(client_sem_token):
    token = criar_token("teste1@contabilidade.com")

    resposta = client_sem_token.get("/me", headers={"Authorization": token})

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Não autenticado"


def test_me_com_token_expirado_devolve_401(client_sem_token):
    # Token montado com expiração no passado, sem esperar as 24h.
    token = criar_token("teste1@contabilidade.com", horas=-1)

    resposta = client_sem_token.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Token inválido ou expirado"


def test_me_com_token_de_usuario_que_nao_existe_no_banco_devolve_401(client_sem_token):
    # Assinatura válida, e-mail que nunca foi semeado: usuario_atual busca no
    # banco a cada requisição, então o token não basta por si só.
    token = criar_token("fantasma@contabilidade.com")

    resposta = client_sem_token.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 401


def test_token_do_login_funciona_no_me(client_sem_token):
    # Fecha o ciclo: o token que /login devolve é aceito por /me.
    token = client_sem_token.post(
        "/login",
        json={"email": "teste2@contabilidade.com", "senha": "teste123"},
    ).json()["token"]

    resposta = client_sem_token.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Usuário Teste 2"


def test_health_check_continua_aberto(client_sem_token):
    resposta = client_sem_token.get("/")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
