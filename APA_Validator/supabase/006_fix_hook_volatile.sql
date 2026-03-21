-- ============================================================
-- Fix: hook STABLE → VOLATILE + manejo de excepciones
-- Un hook que lanza excepción bloquea todo el login.
-- Con EXCEPTION WHEN OTHERS, si falla la búsqueda de universidad
-- el usuario igual puede autenticarse (sin university_id en el JWT).
-- Ejecutar en: Supabase > SQL Editor
-- ============================================================

CREATE OR REPLACE FUNCTION public.get_university_from_email(user_email TEXT)
RETURNS UUID
LANGUAGE SQL
VOLATILE
SECURITY DEFINER
AS $$
    SELECT id
    FROM universities
    WHERE active = true
      AND (
          authorized_domains = '{}'
          OR authorized_domains @> ARRAY[split_part(user_email, '@', 2)]
      )
    ORDER BY (authorized_domains != '{}') DESC
    LIMIT 1;
$$;


CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event JSONB)
RETURNS JSONB
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
AS $$
DECLARE
    claims          JSONB;
    university_uuid UUID;
    user_email      TEXT;
BEGIN
    claims := event -> 'claims';

    user_email := COALESCE(
        event -> 'user_metadata' ->> 'email',
        event -> 'claims'        ->> 'email'
    );

    IF user_email IS NOT NULL THEN
        BEGIN
            university_uuid := public.get_university_from_email(user_email);

            IF university_uuid IS NOT NULL THEN
                claims := jsonb_set(
                    claims,
                    '{app_metadata}',
                    COALESCE(claims -> 'app_metadata', '{}')
                    || jsonb_build_object('university_id', university_uuid)
                );
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Si falla la búsqueda, el usuario igual se autentica sin university_id
            NULL;
        END;
    END IF;

    RETURN jsonb_set(event, '{claims}', claims);
END;
$$;

-- Re-aplicar permisos
GRANT EXECUTE ON FUNCTION public.get_university_from_email    TO supabase_auth_admin;
GRANT EXECUTE ON FUNCTION public.custom_access_token_hook     TO supabase_auth_admin;
REVOKE EXECUTE ON FUNCTION public.custom_access_token_hook    FROM authenticated, anon, public;
GRANT  SELECT  ON TABLE   public.universities                 TO supabase_auth_admin;
