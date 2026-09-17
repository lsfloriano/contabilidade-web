CSV_CONTEUDO = (
    "data,conta_debito,conta_credito,valor,historico\n"
    "2026-01-02,1.1.01,2.3.01,5000,Integralizacao de capital\n"
    "2026-01-05,9.9.99,2.1.01,2000,Conta inexistente\n"
    "2026-01-06,1.1.04,2.1.01,-100,Valor negativo\n"
)

CSV_COM_DATA_INVALIDA = (
    "data,conta_debito,conta_credito,valor,historico\n"
    "2026-01-02,1.1.01,2.3.01,5000,Lancamento valido\n"
    "not-a-date,1.1.04,2.1.01,1000,Data invalida\n"
    "2026-01-06,1.1.01,2.3.01,3000,Outro valido\n"
)


def test_upload_csv_insere_validos_e_reporta_invalidos(client):
    resposta = client.post(
        "/lancamentos/upload",
        files={"arquivo": ("lancamentos.csv", CSV_CONTEUDO, "text/csv")},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["inseridos"] == 1
    assert len(corpo["erros"]) == 2
    assert corpo["erros"][0]["linha"] == 3
    assert corpo["erros"][1]["linha"] == 4

    lancamentos = client.get("/lancamentos").json()
    assert len(lancamentos) == 1
    assert lancamentos[0]["conta_debito"] == "1.1.01"


def test_upload_csv_data_invalida_reporta_erro_por_linha(client):
    resposta = client.post(
        "/lancamentos/upload",
        files={"arquivo": ("lancamentos.csv", CSV_COM_DATA_INVALIDA, "text/csv")},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["inseridos"] == 2
    assert len(corpo["erros"]) == 1
    assert corpo["erros"][0]["linha"] == 3

    lancamentos = client.get("/lancamentos").json()
    assert len(lancamentos) == 2


def test_upload_csv_arquivo_invalido_retorna_400(client):
    resposta = client.post(
        "/lancamentos/upload",
        files={"arquivo": ("invalid.csv", b"", "text/csv")},
    )

    assert resposta.status_code == 400
    assert "CSV inválido" in resposta.json()["detail"]
