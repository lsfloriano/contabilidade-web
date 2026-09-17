from app.db import get_engine, get_sessionmaker, init_db
from app.seed import seed_plano_de_contas
from app.models import ContaContabil


def test_seed_cria_plano_de_contas_padrao():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = get_sessionmaker(engine)
    db = Session()

    seed_plano_de_contas(db)

    contas = db.query(ContaContabil).all()
    assert len(contas) == 20

    caixa = db.query(ContaContabil).filter_by(codigo="1.1.01").first()
    assert caixa.nome == "Caixa"
    assert caixa.natureza.value == "devedora"
    assert caixa.grupo.value == "Ativo Circulante"
    assert caixa.tipo.value == "patrimonial"

    db.close()


def test_seed_e_idempotente():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = get_sessionmaker(engine)
    db = Session()

    seed_plano_de_contas(db)
    seed_plano_de_contas(db)

    assert db.query(ContaContabil).count() == 20
    db.close()
