-- ============================================================
-- Agente APA 7 — Universidad Nacional de Costa Rica (Piloto)
-- Ejecutar en: Supabase > SQL Editor
-- ============================================================

-- Actualizar la universidad demo con los datos reales del piloto
UPDATE universities
SET
    name               = 'Universidad Nacional de Costa Rica',
    country            = 'CR',
    authorized_domains = ARRAY['una.ac.cr'],
    plan_tier          = 'basico',
    primary_color      = '#DA291C',
    active             = true
WHERE id = '7ed65e65-0bd4-48a7-9fb1-47ed2141a660';

-- Verificar el resultado
SELECT id, name, country, authorized_domains, plan_tier, primary_color
FROM universities
WHERE id = '7ed65e65-0bd4-48a7-9fb1-47ed2141a660';
