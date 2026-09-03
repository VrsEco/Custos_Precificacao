# Custos e Precificação

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e . -r requirements.txt
copy .env.example .env
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
