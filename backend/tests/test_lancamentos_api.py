from app.relatorios import montar_balancete


def test_criar_lancamento_valido(client):
    resposta = client.post(
        "/lancamentos",
        json={
            "data": "2026-01-05",
            "conta_debito": "1.1.01",
            "conta_credito": "2.3.01",
            "valor": 1000.0,
            "historico": "Integralização de capital",
        },
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] is not None
    assert corpo["conta_debito"] == "1.1.01"
    assert corpo["conta_credito"] == "2.3.01"


def test_criar_lancamento_conta_inexistente(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "9.9.99", "conta_credito": "2.3.01", "valor": 100.0},
    )
    assert resposta.status_code == 422


def test_criar_lancamento_debito_igual_credito(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "1.1.01", "valor": 100.0},
    )
    assert resposta.status_code == 422


def test_criar_lancamento_valor_invalido(client):
    resposta = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 0},
    )
    assert resposta.status_code == 422


def test_listar_lancamentos_ordenado_por_data(client):
    client.post("/lancamentos", json={"data": "2026-01-10", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 50.0})
    client.post("/lancamentos", json={"data": "2026-01-02", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 20.0})

    resposta = client.get("/lancamentos")
    corpo = resposta.json()
    assert [l["data"] for l in corpo] == ["2026-01-02", "2026-01-10"]


def test_estornar_lancamento_inverte_contas_valor_e_referencia(client):
    original = client.post(
        "/lancamentos",
        json={
            "data": "2026-01-05",
            "conta_debito": "1.1.01",
            "conta_credito": "2.3.01",
            "valor": 1000.0,
            "historico": "Integralização de capital",
        },
    ).json()

    resposta = client.post(f"/lancamentos/{original['id']}/estorno", json={"data": "2026-02-01"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] != original["id"]
    assert corpo["data"] == "2026-02-01"
    assert corpo["conta_debito"] == "2.3.01"  # era o crédito do original
    assert corpo["conta_credito"] == "1.1.01"  # era o débito do original
    assert corpo["valor"] == 1000.0
    assert corpo["estorno_de"] == original["id"]
    assert corpo["historico"] == f"Estorno do lançamento #{original['id']}: Integralização de capital"
    # O original não muda: estorno_de vive só no estorno.
    assert original["estorno_de"] is None


def test_estornar_lancamento_historico_padrao_sem_historico_original(client):
    original = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 50.0},
    ).json()

    resposta = client.post(f"/lancamentos/{original['id']}/estorno", json={"data": "2026-02-01"})

    assert resposta.status_code == 201
    # Sem ": " pendurado no fim quando o original não tinha histórico.
    assert resposta.json()["historico"] == f"Estorno do lançamento #{original['id']}"


def test_estornar_lancamento_respeita_historico_customizado(client):
    original = client.post(
        "/lancamentos",
        json={
            "data": "2026-01-05",
            "conta_debito": "1.1.01",
            "conta_credito": "2.3.01",
            "valor": 50.0,
            "historico": "Integralização de capital",
        },
    ).json()

    resposta = client.post(
        f"/lancamentos/{original['id']}/estorno",
        json={"data": "2026-02-01", "historico": "Estorno por erro de digitação"},
    )

    assert resposta.status_code == 201
    assert resposta.json()["historico"] == "Estorno por erro de digitação"


def test_estornar_lancamento_inexistente_retorna_404(client):
    resposta = client.post("/lancamentos/999/estorno", json={"data": "2026-02-01"})
    assert resposta.status_code == 404


def test_estornar_um_estorno_e_permitido(client):
    # O app não valida lançamento duplicado em lugar nenhum; estornar um
    # estorno (o que recria o lançamento original) segue a mesma regra.
    original = client.post(
        "/lancamentos",
        json={
            "data": "2026-01-05",
            "conta_debito": "1.1.01",
            "conta_credito": "2.3.01",
            "valor": 1000.0,
            "historico": "Integralização de capital",
        },
    ).json()
    estorno = client.post(f"/lancamentos/{original['id']}/estorno", json={"data": "2026-02-01"}).json()

    resposta = client.post(f"/lancamentos/{estorno['id']}/estorno", json={"data": "2026-03-01"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    # Inverter duas vezes volta às contas do original.
    assert corpo["conta_debito"] == "1.1.01"
    assert corpo["conta_credito"] == "2.3.01"
    assert corpo["estorno_de"] == estorno["id"]
    assert corpo["historico"] == (
        f"Estorno do lançamento #{estorno['id']}: "
        f"Estorno do lançamento #{original['id']}: Integralização de capital"
    )


def test_listar_lancamentos_devolve_estorno_de(client):
    original = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 1000.0},
    ).json()
    estorno = client.post(f"/lancamentos/{original['id']}/estorno", json={"data": "2026-02-01"}).json()

    corpo = client.get("/lancamentos").json()

    # Ordenado por data (ordenação já existente da rota): original, depois estorno.
    assert [l["id"] for l in corpo] == [original["id"], estorno["id"]]
    assert corpo[0]["estorno_de"] is None
    assert corpo[1]["estorno_de"] == original["id"]


def test_estorno_zera_o_saldo_das_contas_no_balancete(client, db_session):
    # Teste de fechamento: a prova de que o estorno cancela o original pela
    # própria aritmética da partida dobrada, sem calcular_balancete saber que
    # "estorno" existe.
    #
    # Antes:  1.1.01 débito 1000 / 2.3.01 crédito 1000
    #   Caixa (devedora):  1000 - 0 = 1000
    #   Capital (credora): 1000 - 0 = 1000
    # Depois do estorno (2.3.01 débito 1000 / 1.1.01 crédito 1000):
    #   Caixa:   débitos 1000, créditos 1000 -> saldo 1000 - 1000 = 0
    #   Capital: créditos 1000, débitos 1000 -> saldo 1000 - 1000 = 0
    # Os totais de débito e crédito NÃO zeram: cada conta passa a ter 1000 nos
    # dois lados, e a soma geral do balancete vai de 1000 para 2000. O estorno
    # cancela o saldo, não apaga o movimento.
    original = client.post(
        "/lancamentos",
        json={"data": "2026-01-05", "conta_debito": "1.1.01", "conta_credito": "2.3.01", "valor": 1000.0},
    ).json()

    antes = montar_balancete(db_session)
    caixa_antes = next(c for c in antes["linhas"] if c["codigo"] == "1.1.01")
    capital_antes = next(c for c in antes["linhas"] if c["codigo"] == "2.3.01")
    assert caixa_antes["saldo"] == 1000.00
    assert capital_antes["saldo"] == 1000.00
    assert antes["total_debito"] == 1000.00
    assert antes["total_credito"] == 1000.00

    assert client.post(f"/lancamentos/{original['id']}/estorno", json={"data": "2026-02-01"}).status_code == 201

    depois = montar_balancete(db_session)
    caixa_depois = next(c for c in depois["linhas"] if c["codigo"] == "1.1.01")
    capital_depois = next(c for c in depois["linhas"] if c["codigo"] == "2.3.01")
    assert caixa_depois["saldo"] == 0.0
    assert capital_depois["saldo"] == 0.0
    assert caixa_depois["total_debito"] == 1000.00
    assert caixa_depois["total_credito"] == 1000.00
    assert depois["total_debito"] == 2000.00
    assert depois["total_credito"] == 2000.00
