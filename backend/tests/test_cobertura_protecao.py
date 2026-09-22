# Rede de segurança contra esquecimento: se alguém adicionar uma rota nova
# sem Depends(usuario_atual) ou Depends(exigir_admin), este teste falha. A
# lista de exceções abaixo é o único lugar onde uma rota pode ficar aberta de
# propósito — mantê-la curta e explícita é o que dá valor ao teste.
from fastapi.routing import APIRoute

from app.auth import exigir_admin, usuario_atual
from app.main import app

ROTAS_PUBLICAS = {"/", "/login", "/docs", "/redoc", "/openapi.json"}

FUNCOES_DE_PROTECAO = {usuario_atual, exigir_admin}


def _chamadas_recursivas(dependant):
    """Achata a árvore de dependências de uma rota numa lista de callables,
    incluindo sub-dependências (ex.: exigir_admin depende de usuario_atual)."""
    chamadas = []
    for dependencia in dependant.dependencies:
        chamadas.append(dependencia.call)
        chamadas.extend(_chamadas_recursivas(dependencia))
    return chamadas


def test_toda_rota_fora_da_lista_publica_exige_autenticacao():
    rotas_api = [rota for rota in app.routes if isinstance(rota, APIRoute)]

    # Se a lista de rotas encolher a ponto de não sobrar nenhuma para checar,
    # o teste passaria vazio sem provar nada: melhor falhar alto.
    assert rotas_api, "Nenhuma APIRoute encontrada no app — algo mudou na montagem do app.main"

    rotas_sem_protecao = []
    for rota in rotas_api:
        if rota.path in ROTAS_PUBLICAS:
            continue
        chamadas = _chamadas_recursivas(rota.dependant)
        if not any(chamada in FUNCOES_DE_PROTECAO for chamada in chamadas):
            rotas_sem_protecao.append((rota.path, sorted(rota.methods)))

    assert rotas_sem_protecao == []
