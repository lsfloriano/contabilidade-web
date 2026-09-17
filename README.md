# Contabilidade Web

Aplicação de portfólio que replica o ciclo contábil básico (lançamento →
balancete → Balanço Patrimonial e DRE) com FastAPI + pandas no backend
e React no frontend.

## Rodando o backend

    cd backend
    python -m venv .venv
    .venv/Scripts/activate   # Windows; no POSIX: source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

A API sobe em http://localhost:8000. Os testes: `pytest -v`.

## Rodando o frontend

    cd frontend
    npm install
    npm run dev

O app sobe em http://localhost:5173.

## Checklist de verificação manual (end-to-end)

- [ ] Backend e frontend rodando simultaneamente
- [ ] Aba Lançamentos: dropdowns de conta populados
- [ ] Criar um lançamento manual (ex: débito Caixa, crédito Capital
      Social) e ver aparecer na tabela
- [ ] Upload de CSV com uma linha válida e uma com conta inexistente:
      confirmar que a válida entrou e o erro aponta a linha certa
- [ ] Aba Balancete: saldo da conta lançada bate com o valor informado
- [ ] Aba Balanço Patrimonial: Ativo fecha com Passivo + PL (sem aviso
      de desbalanceamento)
  - **Nota:** Este projeto implementa um período único contínuo, sem fechamento de exercício. Portanto, após lançar qualquer receita ou despesa, o resultado não é automaticamente transferido para Patrimônio Líquido. Assim, o check "Ativo bate com Passivo + PL" mostrará desbalanceamento, o que é o comportamento correto esperado nesta versão 1.
- [ ] Aba DRE: lançar uma receita e uma despesa, conferir que o
      resultado do período é receita - despesa
