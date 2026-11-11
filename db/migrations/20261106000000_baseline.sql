-- Baseline: schema of the shared Postgres (libra_test) as of 2026-11-06,
-- dumped with `pg_dump --schema-only --no-owner --no-privileges --schema=public`.
-- Already applied on the shared DB; only run it against a fresh database.
-- Includes Libra-owned tables (company, job_list, enrichment_examples) because
-- Scales references them directly.

-- migrate:up
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', 'public', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS public;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';

--
-- Name: set_updated_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$;

--
-- Name: upsert_application(uuid, uuid, character varying, character varying, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.upsert_application(p_user_id uuid, p_company uuid, p_role_title character varying, p_sender_email character varying, p_status text, OUT application_id uuid, OUT action text, OUT old_status text, OUT new_status text) RETURNS record
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_current_status   text;
    v_current_priority int;
    v_new_priority     int;
BEGIN
    v_new_priority := CASE p_status
        WHEN 'applied'   THEN 1
        WHEN 'oa'        THEN 2
        WHEN 'interview' THEN 3
        WHEN 'offer'     THEN 4
        WHEN 'rejected'  THEN 5
        WHEN 'ghosted'   THEN 5
        ELSE 0
    END;

    SELECT id, status
      INTO application_id, v_current_status
      FROM application
     WHERE user_id = p_user_id
       AND company = p_company
       AND lower(sender_email) = lower(p_sender_email);

    -- No existing application -> insert a fresh one.
    IF application_id IS NULL THEN
        INSERT INTO application (user_id, company, role_title, sender_email, status)
        VALUES (p_user_id, p_company, p_role_title, p_sender_email, p_status)
        RETURNING id INTO application_id;

        action     := 'inserted';
        old_status := NULL;
        new_status := p_status;
        RETURN;
    END IF;

    v_current_priority := CASE v_current_status
        WHEN 'applied'   THEN 1
        WHEN 'oa'        THEN 2
        WHEN 'interview' THEN 3
        WHEN 'offer'     THEN 4
        WHEN 'rejected'  THEN 5
        WHEN 'ghosted'   THEN 5
        ELSE 0
    END;

    old_status := v_current_status;
    new_status := CASE
        WHEN v_new_priority >= v_current_priority THEN p_status
        ELSE v_current_status
    END;

    UPDATE application
       SET role_title = COALESCE(p_role_title, role_title),
           status     = new_status,
           status_changed_at = CASE
               WHEN new_status IS DISTINCT FROM v_current_status
               THEN now() ELSE status_changed_at
           END,
           updated_at = now()
     WHERE id = application_id;

    action := CASE
        WHEN new_status IS DISTINCT FROM v_current_status THEN 'status_changed'
        ELSE 'updated'
    END;
    RETURN;
END;
$$;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: application; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.application (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    company uuid,
    job_id uuid,
    role_title character varying(1000),
    sender_email character varying(255),
    status text DEFAULT 'applied'::text NOT NULL,
    status_changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

--
-- Name: company; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255),
    company_url character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

--
-- Name: enrichment_examples; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enrichment_examples (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    raw_description text NOT NULL,
    extracted_json jsonb NOT NULL,
    embedding public.vector(768),
    source_job_id uuid,
    verified_by text,
    added_at timestamp with time zone DEFAULT now(),
    demoted boolean DEFAULT false
);

--
-- Name: ignore_list; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ignore_list (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: ignore_list_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ignore_list_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: ignore_list_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ignore_list_id_seq OWNED BY public.ignore_list.id;

--
-- Name: job_list; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.job_list (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    title character varying(1000),
    company uuid,
    location character varying(500),
    is_remote boolean,
    description text,
    apply_url character varying(1000),
    role_type character varying(255),
    pay_range character varying(255),
    source character varying(20),
    tags json,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    enriched boolean DEFAULT false NOT NULL,
    enrich_attempts integer DEFAULT 0,
    status text DEFAULT 'active'::text NOT NULL,
    embedding public.vector(768),
    summary text
);

--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    from_address text,
    subject text,
    body_encrypted text,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    received_at timestamp with time zone DEFAULT now() NOT NULL,
    application_id uuid,
    gmail_message_id text,
    gmail_thread_id text
);

--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    gmail_status character varying(20) DEFAULT 'not_connected'::character varying,
    last_synced_at timestamp with time zone,
    gmail_refresh_token_encrypted text,
    gmail_history_id bigint,
    password character varying(255),
    CONSTRAINT gmail_status_check CHECK (((gmail_status)::text = ANY ((ARRAY['not_connected'::character varying, 'connected'::character varying, 'needs_reauth'::character varying, 'disconnected'::character varying])::text[])))
);

--
-- Name: ignore_list id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ignore_list ALTER COLUMN id SET DEFAULT nextval('public.ignore_list_id_seq'::regclass);

--
-- Name: application application_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application
    ADD CONSTRAINT application_pkey PRIMARY KEY (id);

--
-- Name: company company_name_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company
    ADD CONSTRAINT company_name_unique UNIQUE (name);

--
-- Name: company company_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company
    ADD CONSTRAINT company_pkey PRIMARY KEY (id);

--
-- Name: enrichment_examples enrichment_examples_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrichment_examples
    ADD CONSTRAINT enrichment_examples_pkey PRIMARY KEY (id);

--
-- Name: ignore_list ignore_list_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ignore_list
    ADD CONSTRAINT ignore_list_email_key UNIQUE (email);

--
-- Name: ignore_list ignore_list_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ignore_list
    ADD CONSTRAINT ignore_list_pkey PRIMARY KEY (id);

--
-- Name: job_list job_list_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_list
    ADD CONSTRAINT job_list_pkey PRIMARY KEY (id);

--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);

--
-- Name: enrichment_examples uq_source_job; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrichment_examples
    ADD CONSTRAINT uq_source_job UNIQUE (source_job_id);

--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);

--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

--
-- Name: application_user_id_index; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX application_user_id_index ON public.application USING btree (user_id);

--
-- Name: application_user_job_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX application_user_job_unique ON public.application USING btree (user_id, job_id) WHERE (job_id IS NOT NULL);

--
-- Name: company_location_title_apply_url_1784051293594_index; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX company_location_title_apply_url_1784051293594_index ON public.job_list USING btree (company, location, title, apply_url);

--
-- Name: idx_messages_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_status ON public.messages USING btree (status);

--
-- Name: idx_messages_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_user_id ON public.messages USING btree (user_id);

--
-- Name: messages_application_id_index; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX messages_application_id_index ON public.messages USING btree (application_id);

--
-- Name: messages_user_thread_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX messages_user_thread_idx ON public.messages USING btree (user_id, gmail_thread_id);

--
-- Name: users_email_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX users_email_unique ON public.users USING btree (lower((email)::text));

--
-- Name: company trigger_set_updated_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_set_updated_timestamp BEFORE UPDATE ON public.company FOR EACH ROW EXECUTE FUNCTION public.set_updated_timestamp();

--
-- Name: application application_company_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application
    ADD CONSTRAINT application_company_fkey FOREIGN KEY (company) REFERENCES public.company(id);

--
-- Name: application application_job_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application
    ADD CONSTRAINT application_job_fkey FOREIGN KEY (job_id) REFERENCES public.job_list(id);

--
-- Name: application application_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application
    ADD CONSTRAINT application_user_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

--
-- Name: job_list job_list_company_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_list
    ADD CONSTRAINT job_list_company_fkey FOREIGN KEY (company) REFERENCES public.company(id);

--
-- Name: messages messages_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.application(id) ON DELETE CASCADE;

--
-- Name: messages messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

--
-- Name: messages; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

--
-- Name: messages user_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_isolation ON public.messages USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));

--
-- PostgreSQL database dump complete
--



-- migrate:down
-- Baseline is not reversible.
