from app.db import get_engine, get_sessionmaker, init_db
from app.seed import seed_plano_de_contas, seed_usuarios
from app.models import ContaContabil, Papel, Usuario


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


def test_seed_cria_os_tres_usuarios_fixos():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = get_sessionmaker(engine)
    db = Session()

    seed_usuarios(db)

    usuarios = db.query(Usuario).order_by(Usuario.email).all()
    assert [u.email for u in usuarios] == [
        "admin@contabilidade.com",
        "teste1@contabilidade.com",
        "teste2@contabilidade.com",
    ]
    assert usuarios[0].papel == Papel.admin
    assert usuarios[1].papel == Papel.comum
    assert usuarios[2].papel == Papel.comum
    # A senha nunca fica em claro no banco.
    assert usuarios[0].senha_hash != "admin123"

    db.close()


def test_seed_usuarios_e_idempotente():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = get_sessionmaker(engine)
    db = Session()

    seed_usuarios(db)
    seed_usuarios(db)

    assert db.query(Usuario).count() == 3
    db.close()
