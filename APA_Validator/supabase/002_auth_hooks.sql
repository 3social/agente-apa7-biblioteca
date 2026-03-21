-- ============================================================
-- Agente APA 7 — Auth Hooks: JWT personalizado por dominio
-- Ejecutar en: Supabase > SQL Editor
--
-- Después de ejecutar este script:
--   1. Ve a Authentication > Hooks
--   2. En "Custom Access Token" selecciona: public.custom_access_token_hook
-- ============================================================


-- ── Función 1: Obtener university_id desde el dominio del email ───────────────

CREATE OR REPLACE FUNCTION public.get_university_from_email(user_email TEXT)
RETURNS UUID
LANGUAGE SQL
STABLE
SECURITY DEFINER
AS $$
    SELECT id
    FROM universities
    WHERE active = true
      AND (
          -- Dominio vacío = universidad demo, acepta cualquier email
          authorized_domains = '{}'
          OR
          -- Dominio definido = solo emails de esa institución
          authorized_domains @> ARRAY[split_part(user_email, '@', 2)]
      )
    ORDER BY
        -- Priorizar match exacto de dominio sobre universidad demo
        (authorized_domains != '{}') DESC
    LIMIT 1;
$$;

COMMENT ON FUNCTION public.get_university_from_email IS
    'Retorna el UUID de la universidad que autoriza el dominio del email dado.
     Si la universidad tiene authorized_domains vacío, acepta cualquier email.';


-- ── Función 2: Hook de token personalizado ────────────────────────────────────
-- Se ejecuta cada vez que Supabase genera un JWT (login, refresh).
-- Inyecta university_id en app_metadata para que las políticas RLS funcionen.

CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event JSONB)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    claims          JSONB;
    university_uuid UUID;
    user_email      TEXT;
BEGIN
    claims := event -> 'claims';

    -- Obtener email del usuario (puede estar en distintos lugares según el proveedor)
    user_email := COALESCE(
        event -> 'user_metadata' ->> 'email',
        event -> 'claims' ->> 'email'
    );

    IF user_email IS NOT NULL THEN
        university_uuid := public.get_university_from_email(user_email);

        IF university_uuid IS NOT NULL THEN
            -- Inyectar university_id en app_metadata del JWT
            claims := jsonb_set(
                claims,
                '{app_metadata}',
                COALESCE(claims -> 'app_metadata', '{}')
                || jsonb_build_object('university_id', university_uuid)
            );
        END IF;
    END IF;

    RETURN jsonb_set(event, '{claims}', claims);
END;
$$;

COMMENT ON FUNCTION public.custom_access_token_hook IS
    'Hook de Supabase Auth: agrega university_id al app_metadata del JWT.
     Habilitar en: Authentication > Hooks > Custom Access Token.';

-- Permisos requeridos por Supabase Auth para ejecutar el hook
GRANT EXECUTE ON FUNCTION public.custom_access_token_hook TO supabase_auth_admin;
REVOKE EXECUTE ON FUNCTION public.custom_access_token_hook FROM authenticated, anon, public;

GRANT SELECT ON TABLE public.universities TO supabase_auth_admin;
