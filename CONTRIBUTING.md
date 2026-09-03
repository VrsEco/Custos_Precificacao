# Fluxo de trabalho (2 devs, cada um em sua máquina)

## Branches

- `main` — produção (Fase 3). Protegida; só recebe merge de `staging`.
- `staging` — ambiente de testes (Fase 2). Protegida; só recebe merge de `develop`.
- `develop` — integração da Fase 1 (atual). Onde as features se encontram.
- `feature/<descricao-curta>` — uma branch por tarefa, criada a partir de `develop`.

Por enquanto (Fase 1), só `main` e `develop` existem de fato; `staging` é criada quando o ambiente de testes for provisionado.

## Rotina do dia a dia

1. `git checkout develop && git pull`
2. `git checkout -b feature/nome-da-tarefa`
3. Commits pequenos, mensagens no imperativo (`adiciona cálculo de markup`, não `adicionado`).
4. `git push -u origin feature/nome-da-tarefa`
5. Abrir Pull Request no GitHub apontando para `develop`.
6. O outro dev revisa e aprova antes do merge (branch protection recomendada: exigir 1 review + CI verde).
7. Merge (squash) e apagar a branch da feature.

## Regra de ouro

Nunca commitar direto em `develop`, `staging` ou `main` — sempre via PR, mesmo trabalhando só os dois.
Nunca commitar `.env` (segredos/credenciais de banco) — só `.env.example`.

## Quando a Fase 2 (testes) entrar

- Criar branch `staging` a partir de `develop`.
- Provisionar Postgres de teste; preencher `DATABASE_URL` só no ambiente de CI/deploy de staging (não no repo).
- Configurar branch protection em `staging` igual à de `main`.
