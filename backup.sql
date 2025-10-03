--
-- PostgreSQL database dump
--

\restrict 6pu0I8AfnLU6ckbM9mmUguXOINWrxI9zZ0HQJdd9ejhWgvLOil47KjQpgiHgFq2

-- Dumped from database version 17.6 (Debian 17.6-1.pgdg12+1)
-- Dumped by pg_dump version 17.6 (Ubuntu 17.6-2.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS fk_usuario_objetivo_principal_id_convocatoria;
ALTER TABLE IF EXISTS ONLY public.tema DROP CONSTRAINT IF EXISTS fk_tema_parent_id_tema;
ALTER TABLE IF EXISTS ONLY public.tema DROP CONSTRAINT IF EXISTS fk_tema_bloque_id_bloque;
ALTER TABLE IF EXISTS ONLY public.resultado_test DROP CONSTRAINT IF EXISTS fk_resultado_test_usuario_id_usuario;
ALTER TABLE IF EXISTS ONLY public.resultado_test DROP CONSTRAINT IF EXISTS fk_resultado_test_tema_id_tema;
ALTER TABLE IF EXISTS ONLY public.respuesta_usuario DROP CONSTRAINT IF EXISTS fk_respuesta_usuario_usuario_id_usuario;
ALTER TABLE IF EXISTS ONLY public.respuesta_usuario DROP CONSTRAINT IF EXISTS fk_respuesta_usuario_resultado_test_id_resultado_test;
ALTER TABLE IF EXISTS ONLY public.respuesta_usuario DROP CONSTRAINT IF EXISTS fk_respuesta_usuario_respuesta_seleccionada_id_respuesta;
ALTER TABLE IF EXISTS ONLY public.respuesta_usuario DROP CONSTRAINT IF EXISTS fk_respuesta_usuario_pregunta_id_pregunta;
ALTER TABLE IF EXISTS ONLY public.respuesta DROP CONSTRAINT IF EXISTS fk_respuesta_pregunta_id_pregunta;
ALTER TABLE IF EXISTS ONLY public.pregunta DROP CONSTRAINT IF EXISTS fk_pregunta_tema_id_tema;
ALTER TABLE IF EXISTS ONLY public.nota DROP CONSTRAINT IF EXISTS fk_nota_tema_id_tema;
ALTER TABLE IF EXISTS ONLY public.favoritos DROP CONSTRAINT IF EXISTS fk_favoritos_usuario_id_usuario;
ALTER TABLE IF EXISTS ONLY public.favoritos DROP CONSTRAINT IF EXISTS fk_favoritos_pregunta_id_pregunta;
ALTER TABLE IF EXISTS ONLY public.bloque DROP CONSTRAINT IF EXISTS fk_bloque_convocatoria_id_convocatoria;
ALTER TABLE IF EXISTS ONLY public.accesos_usuario_convocatoria DROP CONSTRAINT IF EXISTS fk_accesos_usuario_convocatoria_usuario_id_usuario;
ALTER TABLE IF EXISTS ONLY public.accesos_usuario_convocatoria DROP CONSTRAINT IF EXISTS fk_accesos_usuario_convocatoria_convocatoria_id_convocatoria;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS uq_usuario_email;
ALTER TABLE IF EXISTS ONLY public.convocatoria DROP CONSTRAINT IF EXISTS uq_convocatoria_nombre;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS pk_usuario;
ALTER TABLE IF EXISTS ONLY public.tema DROP CONSTRAINT IF EXISTS pk_tema;
ALTER TABLE IF EXISTS ONLY public.resultado_test DROP CONSTRAINT IF EXISTS pk_resultado_test;
ALTER TABLE IF EXISTS ONLY public.respuesta_usuario DROP CONSTRAINT IF EXISTS pk_respuesta_usuario;
ALTER TABLE IF EXISTS ONLY public.respuesta DROP CONSTRAINT IF EXISTS pk_respuesta;
ALTER TABLE IF EXISTS ONLY public.pregunta DROP CONSTRAINT IF EXISTS pk_pregunta;
ALTER TABLE IF EXISTS ONLY public.nota DROP CONSTRAINT IF EXISTS pk_nota;
ALTER TABLE IF EXISTS ONLY public.favoritos DROP CONSTRAINT IF EXISTS pk_favoritos;
ALTER TABLE IF EXISTS ONLY public.convocatoria DROP CONSTRAINT IF EXISTS pk_convocatoria;
ALTER TABLE IF EXISTS ONLY public.bloque DROP CONSTRAINT IF EXISTS pk_bloque;
ALTER TABLE IF EXISTS ONLY public.accesos_usuario_convocatoria DROP CONSTRAINT IF EXISTS pk_accesos_usuario_convocatoria;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.usuario ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.tema ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.resultado_test ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.respuesta_usuario ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.respuesta ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.pregunta ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.nota ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.convocatoria ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.bloque ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.usuario_id_seq;
DROP TABLE IF EXISTS public.usuario;
DROP SEQUENCE IF EXISTS public.tema_id_seq;
DROP TABLE IF EXISTS public.tema;
DROP SEQUENCE IF EXISTS public.resultado_test_id_seq;
DROP TABLE IF EXISTS public.resultado_test;
DROP SEQUENCE IF EXISTS public.respuesta_usuario_id_seq;
DROP TABLE IF EXISTS public.respuesta_usuario;
DROP SEQUENCE IF EXISTS public.respuesta_id_seq;
DROP TABLE IF EXISTS public.respuesta;
DROP SEQUENCE IF EXISTS public.pregunta_id_seq;
DROP TABLE IF EXISTS public.pregunta;
DROP SEQUENCE IF EXISTS public.nota_id_seq;
DROP TABLE IF EXISTS public.nota;
DROP TABLE IF EXISTS public.favoritos;
DROP SEQUENCE IF EXISTS public.convocatoria_id_seq;
DROP TABLE IF EXISTS public.convocatoria;
DROP SEQUENCE IF EXISTS public.bloque_id_seq;
DROP TABLE IF EXISTS public.bloque;
DROP TABLE IF EXISTS public.alembic_version;
DROP TABLE IF EXISTS public.accesos_usuario_convocatoria;
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: silvatest_db_nowd_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO silvatest_db_nowd_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accesos_usuario_convocatoria; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.accesos_usuario_convocatoria (
    usuario_id integer NOT NULL,
    convocatoria_id integer NOT NULL,
    fecha_expiracion timestamp without time zone
);


ALTER TABLE public.accesos_usuario_convocatoria OWNER TO silvatest_db_nowd_user;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO silvatest_db_nowd_user;

--
-- Name: bloque; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.bloque (
    id integer NOT NULL,
    nombre character varying(200) NOT NULL,
    posicion integer NOT NULL,
    esta_oculto boolean NOT NULL,
    convocatoria_id integer NOT NULL,
    contexto_ia character varying(250)
);


ALTER TABLE public.bloque OWNER TO silvatest_db_nowd_user;

--
-- Name: bloque_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.bloque_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bloque_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: bloque_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.bloque_id_seq OWNED BY public.bloque.id;


--
-- Name: convocatoria; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.convocatoria (
    id integer NOT NULL,
    nombre character varying(200) NOT NULL,
    es_publica boolean NOT NULL,
    es_premium boolean DEFAULT false NOT NULL
);


ALTER TABLE public.convocatoria OWNER TO silvatest_db_nowd_user;

--
-- Name: convocatoria_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.convocatoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.convocatoria_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: convocatoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.convocatoria_id_seq OWNED BY public.convocatoria.id;


--
-- Name: favoritos; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.favoritos (
    usuario_id integer NOT NULL,
    pregunta_id integer NOT NULL
);


ALTER TABLE public.favoritos OWNER TO silvatest_db_nowd_user;

--
-- Name: nota; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.nota (
    id integer NOT NULL,
    texto text NOT NULL,
    tema_id integer NOT NULL,
    fecha_creacion timestamp without time zone NOT NULL
);


ALTER TABLE public.nota OWNER TO silvatest_db_nowd_user;

--
-- Name: nota_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.nota_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nota_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: nota_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.nota_id_seq OWNED BY public.nota.id;


--
-- Name: pregunta; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.pregunta (
    id integer NOT NULL,
    texto text NOT NULL,
    posicion integer NOT NULL,
    imagen_url character varying(300),
    retroalimentacion text,
    dificultad character varying(50) NOT NULL,
    necesita_revision boolean NOT NULL,
    tema_id integer NOT NULL,
    tipo_pregunta character varying(50) NOT NULL,
    respuesta_correcta_texto character varying(500)
);


ALTER TABLE public.pregunta OWNER TO silvatest_db_nowd_user;

--
-- Name: pregunta_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.pregunta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pregunta_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: pregunta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.pregunta_id_seq OWNED BY public.pregunta.id;


--
-- Name: respuesta; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.respuesta (
    id integer NOT NULL,
    texto text NOT NULL,
    es_correcta boolean NOT NULL,
    pregunta_id integer NOT NULL
);


ALTER TABLE public.respuesta OWNER TO silvatest_db_nowd_user;

--
-- Name: respuesta_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.respuesta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.respuesta_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: respuesta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.respuesta_id_seq OWNED BY public.respuesta.id;


--
-- Name: respuesta_usuario; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.respuesta_usuario (
    id integer NOT NULL,
    es_correcta boolean NOT NULL,
    usuario_id integer NOT NULL,
    pregunta_id integer NOT NULL,
    respuesta_seleccionada_id integer,
    respuesta_texto_usuario character varying(500),
    resultado_test_id integer NOT NULL
);


ALTER TABLE public.respuesta_usuario OWNER TO silvatest_db_nowd_user;

--
-- Name: respuesta_usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.respuesta_usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.respuesta_usuario_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: respuesta_usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.respuesta_usuario_id_seq OWNED BY public.respuesta_usuario.id;


--
-- Name: resultado_test; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.resultado_test (
    id integer NOT NULL,
    nota double precision NOT NULL,
    fecha timestamp without time zone NOT NULL,
    tema_id integer NOT NULL,
    usuario_id integer NOT NULL
);


ALTER TABLE public.resultado_test OWNER TO silvatest_db_nowd_user;

--
-- Name: resultado_test_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.resultado_test_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.resultado_test_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: resultado_test_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.resultado_test_id_seq OWNED BY public.resultado_test.id;


--
-- Name: tema; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.tema (
    id integer NOT NULL,
    nombre character varying(200) NOT NULL,
    posicion integer NOT NULL,
    parent_id integer,
    bloque_id integer,
    es_simulacro boolean NOT NULL,
    tiempo_limite_minutos integer,
    pdf_url character varying(300),
    ruta_documento_contexto character varying(300)
);


ALTER TABLE public.tema OWNER TO silvatest_db_nowd_user;

--
-- Name: tema_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.tema_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tema_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: tema_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.tema_id_seq OWNED BY public.tema.id;


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE TABLE public.usuario (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    email character varying(150) NOT NULL,
    password_hash character varying(128) NOT NULL,
    es_admin boolean NOT NULL,
    recibir_resumen_semanal boolean NOT NULL,
    objetivo_principal_id integer,
    ha_visto_tour boolean DEFAULT false NOT NULL,
    tiene_acceso_ia boolean DEFAULT false NOT NULL,
    preferencias_dashboard json,
    objetivo_fecha date,
    fecha_creacion timestamp without time zone NOT NULL
);


ALTER TABLE public.usuario OWNER TO silvatest_db_nowd_user;

--
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: silvatest_db_nowd_user
--

CREATE SEQUENCE public.usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_id_seq OWNER TO silvatest_db_nowd_user;

--
-- Name: usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER SEQUENCE public.usuario_id_seq OWNED BY public.usuario.id;


--
-- Name: bloque id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.bloque ALTER COLUMN id SET DEFAULT nextval('public.bloque_id_seq'::regclass);


--
-- Name: convocatoria id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.convocatoria ALTER COLUMN id SET DEFAULT nextval('public.convocatoria_id_seq'::regclass);


--
-- Name: nota id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.nota ALTER COLUMN id SET DEFAULT nextval('public.nota_id_seq'::regclass);


--
-- Name: pregunta id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.pregunta ALTER COLUMN id SET DEFAULT nextval('public.pregunta_id_seq'::regclass);


--
-- Name: respuesta id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta ALTER COLUMN id SET DEFAULT nextval('public.respuesta_id_seq'::regclass);


--
-- Name: respuesta_usuario id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta_usuario ALTER COLUMN id SET DEFAULT nextval('public.respuesta_usuario_id_seq'::regclass);


--
-- Name: resultado_test id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.resultado_test ALTER COLUMN id SET DEFAULT nextval('public.resultado_test_id_seq'::regclass);


--
-- Name: tema id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.tema ALTER COLUMN id SET DEFAULT nextval('public.tema_id_seq'::regclass);


--
-- Name: usuario id; Type: DEFAULT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id SET DEFAULT nextval('public.usuario_id_seq'::regclass);


--
-- Data for Name: accesos_usuario_convocatoria; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.accesos_usuario_convocatoria (usuario_id, convocatoria_id, fecha_expiracion) FROM stdin;
\.


--
-- Data for Name: bloque; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.bloque (id, nombre, posicion, esta_oculto, convocatoria_id, contexto_ia) FROM stdin;
\.


--
-- Data for Name: convocatoria; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.convocatoria (id, nombre, es_publica, es_premium) FROM stdin;
\.


--
-- Data for Name: favoritos; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.favoritos (usuario_id, pregunta_id) FROM stdin;
\.


--
-- Data for Name: nota; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.nota (id, texto, tema_id, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: pregunta; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.pregunta (id, texto, posicion, imagen_url, retroalimentacion, dificultad, necesita_revision, tema_id, tipo_pregunta, respuesta_correcta_texto) FROM stdin;
\.


--
-- Data for Name: respuesta; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.respuesta (id, texto, es_correcta, pregunta_id) FROM stdin;
\.


--
-- Data for Name: respuesta_usuario; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.respuesta_usuario (id, es_correcta, usuario_id, pregunta_id, respuesta_seleccionada_id, respuesta_texto_usuario, resultado_test_id) FROM stdin;
\.


--
-- Data for Name: resultado_test; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.resultado_test (id, nota, fecha, tema_id, usuario_id) FROM stdin;
\.


--
-- Data for Name: tema; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.tema (id, nombre, posicion, parent_id, bloque_id, es_simulacro, tiempo_limite_minutos, pdf_url, ruta_documento_contexto) FROM stdin;
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: silvatest_db_nowd_user
--

COPY public.usuario (id, nombre, email, password_hash, es_admin, recibir_resumen_semanal, objetivo_principal_id, ha_visto_tour, tiene_acceso_ia, preferencias_dashboard, objetivo_fecha, fecha_creacion) FROM stdin;
1	Alejandro Fontanil	alejandrofontanil@gmail.com	OAUTH_NO_PASSWORD	t	f	\N	f	f	\N	\N	2025-10-01 14:25:51.823019
2	Alejandro Alonso Fontanil	alesbnk@gmail.com	OAUTH_NO_PASSWORD	f	f	\N	f	t	\N	2026-09-30	2025-10-01 14:26:11.097971
\.


--
-- Name: bloque_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.bloque_id_seq', 1, false);


--
-- Name: convocatoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.convocatoria_id_seq', 1, false);


--
-- Name: nota_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.nota_id_seq', 1, false);


--
-- Name: pregunta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.pregunta_id_seq', 1, false);


--
-- Name: respuesta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.respuesta_id_seq', 1, false);


--
-- Name: respuesta_usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.respuesta_usuario_id_seq', 1, false);


--
-- Name: resultado_test_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.resultado_test_id_seq', 1, false);


--
-- Name: tema_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.tema_id_seq', 1, false);


--
-- Name: usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: silvatest_db_nowd_user
--

SELECT pg_catalog.setval('public.usuario_id_seq', 2, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: accesos_usuario_convocatoria pk_accesos_usuario_convocatoria; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.accesos_usuario_convocatoria
    ADD CONSTRAINT pk_accesos_usuario_convocatoria PRIMARY KEY (usuario_id, convocatoria_id);


--
-- Name: bloque pk_bloque; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.bloque
    ADD CONSTRAINT pk_bloque PRIMARY KEY (id);


--
-- Name: convocatoria pk_convocatoria; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.convocatoria
    ADD CONSTRAINT pk_convocatoria PRIMARY KEY (id);


--
-- Name: favoritos pk_favoritos; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.favoritos
    ADD CONSTRAINT pk_favoritos PRIMARY KEY (usuario_id, pregunta_id);


--
-- Name: nota pk_nota; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.nota
    ADD CONSTRAINT pk_nota PRIMARY KEY (id);


--
-- Name: pregunta pk_pregunta; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.pregunta
    ADD CONSTRAINT pk_pregunta PRIMARY KEY (id);


--
-- Name: respuesta pk_respuesta; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta
    ADD CONSTRAINT pk_respuesta PRIMARY KEY (id);


--
-- Name: respuesta_usuario pk_respuesta_usuario; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta_usuario
    ADD CONSTRAINT pk_respuesta_usuario PRIMARY KEY (id);


--
-- Name: resultado_test pk_resultado_test; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.resultado_test
    ADD CONSTRAINT pk_resultado_test PRIMARY KEY (id);


--
-- Name: tema pk_tema; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.tema
    ADD CONSTRAINT pk_tema PRIMARY KEY (id);


--
-- Name: usuario pk_usuario; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT pk_usuario PRIMARY KEY (id);


--
-- Name: convocatoria uq_convocatoria_nombre; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.convocatoria
    ADD CONSTRAINT uq_convocatoria_nombre UNIQUE (nombre);


--
-- Name: usuario uq_usuario_email; Type: CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT uq_usuario_email UNIQUE (email);


--
-- Name: accesos_usuario_convocatoria fk_accesos_usuario_convocatoria_convocatoria_id_convocatoria; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.accesos_usuario_convocatoria
    ADD CONSTRAINT fk_accesos_usuario_convocatoria_convocatoria_id_convocatoria FOREIGN KEY (convocatoria_id) REFERENCES public.convocatoria(id);


--
-- Name: accesos_usuario_convocatoria fk_accesos_usuario_convocatoria_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.accesos_usuario_convocatoria
    ADD CONSTRAINT fk_accesos_usuario_convocatoria_usuario_id_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: bloque fk_bloque_convocatoria_id_convocatoria; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.bloque
    ADD CONSTRAINT fk_bloque_convocatoria_id_convocatoria FOREIGN KEY (convocatoria_id) REFERENCES public.convocatoria(id);


--
-- Name: favoritos fk_favoritos_pregunta_id_pregunta; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.favoritos
    ADD CONSTRAINT fk_favoritos_pregunta_id_pregunta FOREIGN KEY (pregunta_id) REFERENCES public.pregunta(id);


--
-- Name: favoritos fk_favoritos_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.favoritos
    ADD CONSTRAINT fk_favoritos_usuario_id_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: nota fk_nota_tema_id_tema; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.nota
    ADD CONSTRAINT fk_nota_tema_id_tema FOREIGN KEY (tema_id) REFERENCES public.tema(id);


--
-- Name: pregunta fk_pregunta_tema_id_tema; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.pregunta
    ADD CONSTRAINT fk_pregunta_tema_id_tema FOREIGN KEY (tema_id) REFERENCES public.tema(id);


--
-- Name: respuesta fk_respuesta_pregunta_id_pregunta; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta
    ADD CONSTRAINT fk_respuesta_pregunta_id_pregunta FOREIGN KEY (pregunta_id) REFERENCES public.pregunta(id);


--
-- Name: respuesta_usuario fk_respuesta_usuario_pregunta_id_pregunta; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta_usuario
    ADD CONSTRAINT fk_respuesta_usuario_pregunta_id_pregunta FOREIGN KEY (pregunta_id) REFERENCES public.pregunta(id);


--
-- Name: respuesta_usuario fk_respuesta_usuario_respuesta_seleccionada_id_respuesta; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta_usuario
    ADD CONSTRAINT fk_respuesta_usuario_respuesta_seleccionada_id_respuesta FOREIGN KEY (respuesta_seleccionada_id) REFERENCES public.respuesta(id);


--
-- Name: respuesta_usuario fk_respuesta_usuario_resultado_test_id_resultado_test; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta_usuario
    ADD CONSTRAINT fk_respuesta_usuario_resultado_test_id_resultado_test FOREIGN KEY (resultado_test_id) REFERENCES public.resultado_test(id);


--
-- Name: respuesta_usuario fk_respuesta_usuario_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.respuesta_usuario
    ADD CONSTRAINT fk_respuesta_usuario_usuario_id_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: resultado_test fk_resultado_test_tema_id_tema; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.resultado_test
    ADD CONSTRAINT fk_resultado_test_tema_id_tema FOREIGN KEY (tema_id) REFERENCES public.tema(id);


--
-- Name: resultado_test fk_resultado_test_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.resultado_test
    ADD CONSTRAINT fk_resultado_test_usuario_id_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: tema fk_tema_bloque_id_bloque; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.tema
    ADD CONSTRAINT fk_tema_bloque_id_bloque FOREIGN KEY (bloque_id) REFERENCES public.bloque(id);


--
-- Name: tema fk_tema_parent_id_tema; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.tema
    ADD CONSTRAINT fk_tema_parent_id_tema FOREIGN KEY (parent_id) REFERENCES public.tema(id);


--
-- Name: usuario fk_usuario_objetivo_principal_id_convocatoria; Type: FK CONSTRAINT; Schema: public; Owner: silvatest_db_nowd_user
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_objetivo_principal_id_convocatoria FOREIGN KEY (objetivo_principal_id) REFERENCES public.convocatoria(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO silvatest_db_nowd_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO silvatest_db_nowd_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO silvatest_db_nowd_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO silvatest_db_nowd_user;


--
-- PostgreSQL database dump complete
--

\unrestrict 6pu0I8AfnLU6ckbM9mmUguXOINWrxI9zZ0HQJdd9ejhWgvLOil47KjQpgiHgFq2

