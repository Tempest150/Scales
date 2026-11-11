-- Create a limited login for one developer on the shared DB.
-- They can read/write data but cannot change the schema, drop tables, or manage roles.
--
-- Run as the DB owner (once per developer):
--   psql "$DATABASE_URL" -v dev_user=alice -v dev_password='choose-a-strong-one' -f db/create_dev_user.sql
--
-- Revoke later:
--   REASSIGN OWNED BY alice TO <owner>; DROP OWNED BY alice; DROP ROLE alice;
--
-- NOTE: public.messages has row-level security (policy user_isolation, keyed on
-- current_setting('app.current_user_id')). The table owner bypasses it, but this role
-- will not: queries touching messages fail until either the app sets
-- app.current_user_id per request, or a superuser runs:  ALTER ROLE <dev_user> BYPASSRLS;

\set ON_ERROR_STOP on

CREATE ROLE :"dev_user" LOGIN PASSWORD :'dev_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'dev_user') \gexec

GRANT USAGE ON SCHEMA public TO :"dev_user";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"dev_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"dev_user";
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO :"dev_user";

-- Tables created later by the owner get the same grants automatically.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"dev_user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO :"dev_user";
