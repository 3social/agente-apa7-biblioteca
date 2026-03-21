-- ============================================================
-- Fix: permisos faltantes para el custom_access_token_hook
-- El hook llama a get_university_from_email pero no tenía
-- permiso de ejecución sobre esa función.
-- Ejecutar en: Supabase > SQL Editor
-- ============================================================

GRANT EXECUTE ON FUNCTION public.get_university_from_email TO supabase_auth_admin;
