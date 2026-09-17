def test_listar_contas_retorna_plano_padrao(client):
    resposta = client.get("/contas")
    assert resposta.status_code == 200

    contas = resposta.json()
    assert len(contas) == 20

    caixa = next(c for c in contas if c["codigo"] == "1.1.01")
    assert caixa["nome"] == "Caixa"
    assert caixa["natureza"] == "devedora"
    assert caixa["grupo"] == "Ativo Circulante"
    assert caixa["tipo"] == "patrimonial"
