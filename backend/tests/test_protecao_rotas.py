# Uma rota de cada verbo/rota protegida, sem token: todas param em 401 antes
# de tocar no banco. Com token de conta comum, seguem funcionando como antes.


def test_listar_contas_sem_token_devolve_401(client_sem_token):
    assert client_sem_token.get("/contas").status_code == 401


def test_listar_contas_com_token_comum_devolve_200(client):
    assert client.get("/contas").status_code == 200


def test_listar_lancamentos_sem_token_devolve_401(client_sem_token):
    assert client_sem_token.get("/lancamentos").status_code == 401


def test_listar_lancamentos_com_token_comum_devolve_200(client):
    assert client.get("/lancamentos").status_code == 200


def test_criar_lancamento_sem_token_devolve_401(client_sem_token):
    resposta = client_sem_token.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 100.0},
    )

    assert resposta.status_code == 401


def test_estornar_lancamento_sem_token_devolve_401(client_sem_token):
    resposta = client_sem_token.post("/lancamentos/1/estorno", json={"data": "2026-02-01"})

    # 401 e não 404: a autenticação barra antes de a rota procurar o
    # lançamento #1, que nem existe nesta base.
    assert resposta.status_code == 401


def test_upload_lancamentos_sem_token_devolve_401(client_sem_token):
    resposta = client_sem_token.post(
        "/lancamentos/upload",
        files={"arquivo": ("teste.csv", b"data,conta_debito,conta_credito,valor\n", "text/csv")},
    )

    assert resposta.status_code == 401


def test_lancamentos_com_token_expirado_devolve_401(client_sem_token):
    from app.auth import criar_token

    token = criar_token("teste1@contabilidade.com", horas=-1)

    resposta = client_sem_token.get("/lancamentos", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 401


# As oito rotas de /relatorios, uma a uma: nenhuma escapa da exigência de
# token. As três de exportação entram na mesma lista — hoje o frontend as
# abre por <a href download>, que não carrega header; ver a questão aberta
# registrada no plano.
ROTAS_DE_RELATORIO = [
    "/relatorios/balancete",
    "/relatorios/bp",
    "/relatorios/dre",
    "/relatorios/dfc",
    "/relatorios/analise",
    "/relatorios/balancete/exportar",
    "/relatorios/bp/exportar",
    "/relatorios/dre/exportar",
]


def test_relatorios_sem_token_devolvem_401(client_sem_token):
    for rota in ROTAS_DE_RELATORIO:
        assert client_sem_token.get(rota).status_code == 401, rota


def test_relatorios_com_token_comum_devolvem_200(client):
    # Um lancamento antes: com a base vazia, alguns relatorios exercitam
    # caminhos de divisao por zero que nao sao o objeto deste teste.
    client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 1000.0},
    )

    for rota in ROTAS_DE_RELATORIO:
        assert client.get(rota).status_code == 200, rota
