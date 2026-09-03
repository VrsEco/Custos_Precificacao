# Migrations (placeholder — Fase 2/3)

Esta pasta fica vazia até o Postgres de teste ser provisionado.

Quando chegar a hora:

1. `pip install -r requirements-db.txt`
2. `alembic init migrations` (ou apontar `alembic.ini` para esta pasta)
3. Configurar `sqlalchemy.url` do Alembic para ler `DATABASE_URL` do ambiente (dev/test/prod), nunca hardcoded.
4. Cada mudança de schema vira uma migration versionada aqui, revisada em PR como qualquer código.
