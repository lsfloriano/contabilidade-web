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
