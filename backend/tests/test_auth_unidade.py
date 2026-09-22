import jwt

from app.auth import (
    ALGORITMO_JWT,
    SEGREDO_JWT,
    criar_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)


def test_hash_senha_confere_com_a_senha_certa():
    senha_hash = hash_senha("teste123")

    assert senha_hash != "teste123"
    assert verificar_senha("teste123", senha_hash) is True


def test_hash_senha_recusa_senha_errada():
    senha_hash = hash_senha("teste123")

    assert verificar_senha("teste124", senha_hash) is False


def test_hash_da_mesma_senha_duas_vezes_gera_hashes_diferentes():
    # bcrypt sorteia um salt por chamada; os dois hashes conferem com a
    # mesma senha mesmo sendo textos distintos.
    primeiro = hash_senha("teste123")
    segundo = hash_senha("teste123")

    assert primeiro != segundo
    assert verificar_senha("teste123", primeiro) is True
    assert verificar_senha("teste123", segundo) is True


def test_token_carrega_apenas_sub_e_exp():
    token = criar_token("teste1@contabilidade.com")

    payload = jwt.decode(token, SEGREDO_JWT, algorithms=[ALGORITMO_JWT])

    assert payload["sub"] == "teste1@contabilidade.com"
    assert set(payload.keys()) == {"sub", "exp"}


def test_decodificar_token_devolve_o_email():
    token = criar_token("teste1@contabilidade.com")

    assert decodificar_token(token) == "teste1@contabilidade.com"


def test_decodificar_token_malformado_devolve_none():
    assert decodificar_token("isto-nao-e-um-token") is None


def test_decodificar_token_assinado_com_outro_segredo_devolve_none():
    token = jwt.encode({"sub": "invasor@x.com"}, "outro-segredo", algorithm=ALGORITMO_JWT)

    assert decodificar_token(token) is None


def test_decodificar_token_expirado_devolve_none():
    # Expiração no passado, construída na hora: prova que o prazo é
    # respeitado sem esperar as 24h de verdade.
    token = criar_token("teste1@contabilidade.com", horas=-1)

    assert decodificar_token(token) is None
