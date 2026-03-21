-- ============================================================
-- Agente APA 7 — Esquema inicial multitenant
-- Ejecutar en: Supabase > SQL Editor
-- ============================================================


-- ── Limpiar estado anterior ───────────────────────────────────────────────────

DROP TABLE IF EXISTS apa_errors    CASCADE;
DROP TABLE IF EXISTS documents     CASCADE;
DROP TABLE IF EXISTS universities  CASCADE;
DROP TABLE IF EXISTS revisiones_apa CASCADE;


-- ── Tabla 1: universities (tenants) ──────────────────────────────────────────

CREATE TABLE universities (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name               TEXT        NOT NULL,
    country            TEXT        NOT NULL DEFAULT 'US',
    authorized_domains TEXT[]      NOT NULL DEFAULT '{}',
    plan_tier          TEXT        NOT NULL DEFAULT 'basico'
                                   CHECK (plan_tier IN ('basico', 'profesional', 'institucional')),
    logo_url           TEXT,
    primary_color      TEXT        DEFAULT '#1E3A5F',
    active             BOOLEAN     NOT NULL DEFAULT true,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  universities                    IS 'Instituciones universitarias registradas (tenants).';
COMMENT ON COLUMN universities.authorized_domains IS 'Dominios de email autorizados, ej: {ucr.ac.cr, ucr.edu}';
COMMENT ON COLUMN universities.plan_tier          IS 'Nivel de suscripción: basico | profesional | institucional';


-- ── Tabla 2: documents (documentos analizados) ───────────────────────────────

CREATE TABLE documents (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id    UUID        NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    filename         TEXT        NOT NULL,
    uploaded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    puntaje_apa      INTEGER     NOT NULL DEFAULT 0 CHECK (puntaje_apa BETWEEN 0 AND 100),
    total_errores    INTEGER     NOT NULL DEFAULT 0,
    errores_criticos INTEGER     NOT NULL DEFAULT 0,
    errores_menores  INTEGER     NOT NULL DEFAULT 0,
    -- Errores de módulos opcionales almacenados como JSONB
    -- Se normalizarán en Fase 12 cuando tengamos patrones reales del piloto
    errores_formato  JSONB,
    errores_estilo   JSONB
);

COMMENT ON TABLE  documents                 IS 'Documentos analizados por institución.';
COMMENT ON COLUMN documents.errores_formato IS 'Salida de document_formatter.py (Fase 0.3). NULL si el módulo no estaba activo.';
COMMENT ON COLUMN documents.errores_estilo  IS 'Salida de academic_style.py (Fase 0.4). NULL si el módulo no estaba activo.';

CREATE INDEX idx_documents_university ON documents(university_id);
CREATE INDEX idx_documents_uploaded   ON documents(uploaded_at DESC);


-- ── Tabla 3: apa_errors (errores de citas y referencias, normalizados) ───────

CREATE TABLE apa_errors (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL,
    severidad   TEXT NOT NULL CHECK (severidad IN ('alta', 'media', 'baja')),
    regla_apa   TEXT,
    fragmento   TEXT,
    sugerencia  TEXT
);

COMMENT ON TABLE apa_errors IS 'Errores APA de citas y referencias, normalizados para analítica.';

CREATE INDEX idx_apa_errors_document  ON apa_errors(document_id);
CREATE INDEX idx_apa_errors_tipo      ON apa_errors(tipo);
CREATE INDEX idx_apa_errors_severidad ON apa_errors(severidad);


-- ── Row Level Security ────────────────────────────────────────────────────────
-- El backend Python usa la SERVICE_ROLE key, que bypasea RLS automáticamente.
-- Las políticas siguientes se aplican a usuarios autenticados (Fase 10.3).

ALTER TABLE universities ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents    ENABLE ROW LEVEL SECURITY;
ALTER TABLE apa_errors   ENABLE ROW LEVEL SECURITY;

-- universities: solo superadmin (service_role) puede gestionar.
-- Usuarios autenticados pueden leer su propia institución.
CREATE POLICY "universities_select_own"
    ON universities FOR SELECT
    USING (
        id = (auth.jwt() -> 'app_metadata' ->> 'university_id')::uuid
    );

-- documents: cada universidad ve solo sus documentos.
CREATE POLICY "documents_select_own"
    ON documents FOR SELECT
    USING (
        university_id = (auth.jwt() -> 'app_metadata' ->> 'university_id')::uuid
    );

-- apa_errors: accesibles si el documento pertenece a la universidad del usuario.
CREATE POLICY "apa_errors_select_own"
    ON apa_errors FOR SELECT
    USING (
        document_id IN (
            SELECT id FROM documents
            WHERE university_id = (auth.jwt() -> 'app_metadata' ->> 'university_id')::uuid
        )
    );


-- ── Universidad demo (para desarrollo local y piloto) ────────────────────────
-- Reemplazar con los datos reales de la universidad piloto.

INSERT INTO universities (name, country, authorized_domains, plan_tier)
VALUES ('Universidad Demo', 'US', '{}', 'profesional')
RETURNING id;
-- ⚠️ Copia el UUID retornado y ponlo en tu .env como UNIVERSITY_ID=<uuid>
