from app.auth import hash_senha
from app.models import ContaContabil, Natureza, Grupo, Papel, TipoConta, Usuario

PLANO_DE_CONTAS_PADRAO = [
    # Ativo Circulante
    {"codigo": "1.1.01", "nome": "Caixa", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.1.02", "nome": "Bancos", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.1.03", "nome": "Clientes", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.1.04", "nome": "Estoques", "natureza": Natureza.devedora, "grupo": Grupo.ativo_circulante, "tipo": TipoConta.patrimonial},
    # Ativo Não Circulante
    {"codigo": "1.2.01", "nome": "Imobilizado", "natureza": Natureza.devedora, "grupo": Grupo.ativo_nao_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "1.2.02", "nome": "Investimentos", "natureza": Natureza.devedora, "grupo": Grupo.ativo_nao_circulante, "tipo": TipoConta.patrimonial},
    # Passivo Circulante
    {"codigo": "2.1.01", "nome": "Fornecedores", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "2.1.02", "nome": "Empréstimos CP", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "2.1.03", "nome": "Salários a Pagar", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    {"codigo": "2.1.04", "nome": "Impostos a Pagar", "natureza": Natureza.credora, "grupo": Grupo.passivo_circulante, "tipo": TipoConta.patrimonial},
    # Passivo Não Circulante
    {"codigo": "2.2.01", "nome": "Empréstimos LP", "natureza": Natureza.credora, "grupo": Grupo.passivo_nao_circulante, "tipo": TipoConta.patrimonial},
    # Patrimônio Líquido
    {"codigo": "2.3.01", "nome": "Capital Social", "natureza": Natureza.credora, "grupo": Grupo.patrimonio_liquido, "tipo": TipoConta.patrimonial},
    {"codigo": "2.3.02", "nome": "Lucros/Prejuízos Acumulados", "natureza": Natureza.credora, "grupo": Grupo.patrimonio_liquido, "tipo": TipoConta.patrimonial},
    # Receita
    {"codigo": "3.1.01", "nome": "Receita de Vendas", "natureza": Natureza.credora, "grupo": Grupo.receita, "tipo": TipoConta.resultado},
    {"codigo": "3.1.02", "nome": "Receita de Serviços", "natureza": Natureza.credora, "grupo": Grupo.receita, "tipo": TipoConta.resultado},
    # Despesa
    {"codigo": "4.1.01", "nome": "CMV", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.02", "nome": "Despesas Administrativas", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.03", "nome": "Despesas com Vendas", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.04", "nome": "Despesas Financeiras", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
    {"codigo": "4.1.05", "nome": "Impostos sobre Vendas", "natureza": Natureza.devedora, "grupo": Grupo.despesa, "tipo": TipoConta.resultado},
]


def seed_plano_de_contas(db):
    if db.query(ContaContabil).count() > 0:
        return
    for conta in PLANO_DE_CONTAS_PADRAO:
        db.add(ContaContabil(**conta))
    db.commit()


# Três contas fixas, semeadas como o plano de contas: não existe cadastro
# público neste app. A senha em claro vive só aqui, para o seed hashear;
# o banco guarda apenas o hash.
USUARIOS_PADRAO = [
    {"email": "admin@contabilidade.com", "nome": "Administrador", "senha": "admin123", "papel": Papel.admin},
    {"email": "teste1@contabilidade.com", "nome": "Usuário Teste 1", "senha": "teste123", "papel": Papel.comum},
    {"email": "teste2@contabilidade.com", "nome": "Usuário Teste 2", "senha": "teste123", "papel": Papel.comum},
]


def seed_usuarios(db):
    if db.query(Usuario).count() > 0:
        return
    for usuario in USUARIOS_PADRAO:
        db.add(Usuario(
            email=usuario["email"],
            nome=usuario["nome"],
            senha_hash=hash_senha(usuario["senha"]),
            papel=usuario["papel"],
        ))
    db.commit()
