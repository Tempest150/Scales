# Database

Scales uses the shared Postgres configured in `backend/.env`. Schema changes go
through [dbmate](https://github.com/amacneil/dbmate) migrations in `db/migrations/`,
instead of hand-run statements against the live DB.

## Everyday use

All commands run in Docker and read `DATABASE_URL` from `backend/.env`:

```
docker compose run --rm migrate status            # what's applied / pending
docker compose run --rm migrate new add_notes_idx  # creates db/migrations/<timestamp>_add_notes_idx.sql
docker compose run --rm migrate up                 # apply pending migrations
docker compose run --rm migrate rollback           # undo the last one
```

A migration file has two sections:

```sql
-- migrate:up
CREATE INDEX application_status_idx ON application (status);

-- migrate:down
DROP INDEX application_status_idx;
```

CI applies every migration to a fresh Postgres on each PR, so broken SQL fails
there before anyone runs it against the shared DB.

## Baseline

`20261106000000_baseline.sql` is a `pg_dump --schema-only` of the shared DB taken
on 2026-11-06. It already matches the live schema, so it must be **marked as
applied there once** rather than run. Do this once, as the DB owner:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (version varchar(128) PRIMARY KEY);
INSERT INTO schema_migrations (version) VALUES ('20261106000000') ON CONFLICT DO NOTHING;
```

After that, `migrate status` shows the baseline as applied, and `migrate up`
only runs new migrations. Running the baseline against the live DB without this
step fails harmlessly: it runs in a transaction and stops at the first
`CREATE TABLE` that already exists.

## Giving another developer access

Don't share the owner login. Create a limited user per developer instead. It
can read and write data but can't change the schema or drop anything:

```
psql "$DATABASE_URL" -v dev_user=alice -v dev_password='strong-password' -f db/create_dev_user.sql
```

Then give them their own `PGUSER`/`PGPASSWORD` for `backend/.env`. The script's
header covers revoking access, and a caveat about the row-level security
on `messages`.
