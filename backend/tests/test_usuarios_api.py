NOVO_USUARIO = {
    "email": "novo@contabilidade.com",
    "nome": "Conta Nova",
    "senha": "novo123",
    "papel": "comum",
}


def test_listar_usuarios_sem_token_devolve_401(client_sem_token):
    assert client_sem_token.get("/usuarios").status_code == 401


def test_listar_usuarios_com_token_comum_devolve_403(client):
    resposta = client.get("/usuarios")

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Acesso restrito a administradores"


def test_listar_usuarios_com_token_admin_devolve_os_tres_semeados(client_admin):
    resposta = client_admin.get("/usuarios")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert [u["email"] for u in corpo] == [
        "admin@contabilidade.com",
        "teste1@contabilidade.com",
        "teste2@contabilidade.com",
    ]
    assert corpo[0]["nome"] == "Administrador"
    assert corpo[0]["papel"] == "admin"
    assert corpo[1]["papel"] == "comum"
    # O hash nunca sai na resposta.
    assert "senha_hash" not in corpo[0]
    assert "senha" not in corpo[0]


def test_criar_usuario_sem_token_devolve_401(client_sem_token):
    assert client_sem_token.post("/usuarios", json=NOVO_USUARIO).status_code == 401


def test_criar_usuario_com_token_comum_devolve_403(client):
    assert client.post("/usuarios", json=NOVO_USUARIO).status_code == 403


def test_criar_usuario_com_token_admin_devolve_201(client_admin):
    resposta = client_admin.post("/usuarios", json=NOVO_USUARIO)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] is not None
    assert corpo["email"] == "novo@contabilidade.com"
    assert corpo["nome"] == "Conta Nova"
    assert corpo["papel"] == "comum"


def test_usuario_criado_aparece_na_listagem(client_admin):
    client_admin.post("/usuarios", json=NOVO_USUARIO)

    corpo = client_admin.get("/usuarios").json()

    # Ordenado por e-mail: "admin" < "novo" < "teste1" < "teste2".
    assert [u["email"] for u in corpo] == [
        "admin@contabilidade.com",
        "novo@contabilidade.com",
        "teste1@contabilidade.com",
        "teste2@contabilidade.com",
    ]


def test_usuario_criado_consegue_fazer_login(client_admin, client_sem_token):
    # Prova que a senha foi hasheada com o mesmo esquema que /login verifica.
    client_admin.post("/usuarios", json=NOVO_USUARIO)

    resposta = client_sem_token.post(
        "/login",
        json={"email": "novo@contabilidade.com", "senha": "novo123"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["papel"] == "comum"


def test_criar_usuario_admin_pelo_endpoint(client_admin, client_sem_token):
    client_admin.post(
        "/usuarios",
        json={"email": "admin2@contabilidade.com", "nome": "Admin Dois", "senha": "admin456", "papel": "admin"},
    )

    token = client_sem_token.post(
        "/login",
        json={"email": "admin2@contabilidade.com", "senha": "admin456"},
    ).json()["token"]

    resposta = client_sem_token.get("/usuarios", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200


def test_criar_usuario_com_email_duplicado_devolve_422(client_admin):
    resposta = client_admin.post(
        "/usuarios",
        json={"email": "teste1@contabilidade.com", "nome": "Duplicado", "senha": "x123456", "papel": "comum"},
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "e-mail teste1@contabilidade.com já cadastrado"


def test_criar_usuario_com_papel_invalido_devolve_422(client_admin):
    resposta = client_admin.post(
        "/usuarios",
        json={"email": "outro@contabilidade.com", "nome": "Outro", "senha": "x123456", "papel": "chefe"},
    )

    assert resposta.status_code == 422


def test_criar_usuario_com_senha_curta_devolve_422(client_admin):
    resposta = client_admin.post(
        "/usuarios",
        json={"email": "curta@contabilidade.com", "nome": "Senha Curta", "senha": "123", "papel": "comum"},
    )

    assert resposta.status_code == 422


def test_criar_usuario_com_email_duplicado_em_caixa_diferente_devolve_422(client_admin):
    resposta = client_admin.post(
        "/usuarios",
        json={"email": "Teste1@Contabilidade.com", "nome": "Duplicado", "senha": "x123456", "papel": "comum"},
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "e-mail teste1@contabilidade.com já cadastrado"


def test_mudanca_de_papel_vale_na_requisicao_seguinte(client, db_session):
    # O token de `client` é de conta comum e não muda; o papel vem do banco a
    # cada requisição. Promovida a admin, a MESMA credencial passa a entrar
    # em /usuarios — que é justamente a razão de o papel não ir no token.
    from app.models import Papel, Usuario

    assert client.get("/usuarios").status_code == 403

    usuario = db_session.query(Usuario).filter_by(email="teste1@contabilidade.com").first()
    usuario.papel = Papel.admin
    db_session.commit()

    assert client.get("/usuarios").status_code == 200


def test_rebaixamento_de_papel_vale_na_requisicao_seguinte(client_admin, db_session):
    # Espelho do teste acima: o token de `client_admin` é de conta admin e não
    # muda; rebaixada a comum, a MESMA credencial perde acesso a /usuarios já
    # na próxima requisição, sem esperar o token expirar.
    from app.models import Papel, Usuario

    assert client_admin.get("/usuarios").status_code == 200

    usuario = db_session.query(Usuario).filter_by(email="admin@contabilidade.com").first()
    usuario.papel = Papel.comum
    db_session.commit()

    assert client_admin.get("/usuarios").status_code == 403
