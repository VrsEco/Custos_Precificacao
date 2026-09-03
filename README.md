# Custos e Precificação

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e . -r requirements.txt
copy .env.example .env
```

A partir do motor de custeio (schema + cálculo + CLI), o projeto passou a depender de um Postgres local. Antes de rodar os testes:

1. Tenha um PostgreSQL rodando localmente.
2. Crie uma role e um banco dedicados ao projeto (não use o superusuário `postgres` direto):
   ```sql
   CREATE ROLE custos_precificacao WITH LOGIN PASSWORD 'escolha_uma_senha' NOSUPERUSER NOCREATEDB NOCREATEROLE;
   CREATE DATABASE custos_precificacao_dev OWNER custos_precificacao;
   ```
3. Ajuste `DATABASE_URL` no `.env` com o usuário/senha/porta que você criou:
   ```
   DATABASE_URL=postgresql+psycopg2://custos_precificacao:SENHA@localhost:5432/custos_precificacao_dev
   ```
4. Rode as migrations para criar o schema:
   ```bash
   python -m alembic upgrade head
   ```

Só então rode os testes:

```bash
pytest
```

## Ambientes (roadmap)

O projeto evolui em 3 fases. Cada fase liga uma branch a um ambiente e (a partir da Fase 2) a um banco Postgres próprio.

| Fase | Branch      | Ambiente          | Banco Postgres        | Status |
|------|-------------|--------------------|------------------------|--------|
| 1    | `develop`   | Desenvolvimento    | local por dev (opcional) | ✅ ativo |
| 2    | `staging`   | Testes             | Postgres de teste       | 🔜 planejado |
| 3    | `main`      | Produção           | Postgres de produção    | 🔜 planejado |

Fluxo de promoção: `feature/*` → PR → `develop` → PR → `staging` → PR → `main`.

Cada ambiente lê sua config via variáveis de ambiente (`APP_ENV`, `DATABASE_URL`), nunca hardcoded — ver [.env.example](.env.example). Detalhes do fluxo de trabalho em [CONTRIBUTING.md](CONTRIBUTING.md).
