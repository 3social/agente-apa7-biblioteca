-- ============================================================
-- Fix: permitir lectura pública de universities para el login
-- El dominio autorizado no es dato sensible — es necesario
-- para validar el email antes de enviar el OTP.
-- Ejecutar en: Supabase > SQL Editor
-- ============================================================

CREATE POLICY "universities_public_domain_check"
    ON universities FOR SELECT
    TO anon
    USING (active = true);
