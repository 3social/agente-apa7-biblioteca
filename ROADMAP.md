# Roadmap de Evolución: De Prototipo a SaaS Académico
### Agente APA 7 — Plataforma Institucional de Revisión Académica

> **Objetivo estratégico:** Plataforma SaaS multi-institución para bibliotecas universitarias en Latinoamérica,
> con analítica institucional, arquitectura desacoplada y autenticación por dominio universitario.

---

## Estado Actual

| Componente | Estado |
|---|---|
| Validador APA 7 con IA (GPT-4o-mini, Structured Outputs) | ✅ Operativo |
| RAG sobre Manual APA 7 (FAISS en memoria) | ✅ Operativo |
| Validación de formato físico sin LLM (python-docx) | ✅ Operativo |
| Estilo académico APA 7 (LLM — opcional) | ✅ Operativo |
| Core Engine desacoplado de UI | ✅ Operativo |
| API REST FastAPI | ✅ Operativo |
| Autenticación OTP por dominio universitario | ✅ Operativo |
| Esquema multitenant + RLS en Supabase | ✅ Operativo |
| Branding institucional en reportes Word | ✅ Operativo |
| Gestión de cuotas por plan | ✅ Operativo |
| Piloto Universidad Nacional de Costa Rica | ✅ Activo |

---

## Fases Completadas

### Fase 0 — Producto Base

| Sub-fase | Descripción | Estado |
|---|---|---|
| 0.1 | Output JSON estructurado (Pydantic + Structured Outputs) | ✅ |
| 0.2 | Feature flags + RAG por sección + Extractor completo | ✅ |
| 0.3 | `document_formatter.py` — formato físico sin LLM | ✅ |
| 0.4 | `academic_style.py` — estilo académico APA 7 (opcional) | ✅ |
| 0.5 | Coherencia semántica | Descartado — no aplica para adelantos |

### Fase 9 — Desacoplamiento y API

- `core/engine.py` — orquestador sin dependencias de UI
- `api/main.py` — FastAPI: `POST /analyze`, `GET /health`
- Streamlit funciona como cliente del engine

### Fase 10 — Infraestructura SaaS

- Esquema multitenant: `universities`, `documents`, `apa_errors`
- Row Level Security con `university_id` en JWT
- Autenticación OTP por dominio universitario (Supabase Auth)
- pgvector habilitado (migración RAG diferida a post-piloto)

### Fase 11 — Piloto UNA Costa Rica

- Branding: logo, Rojo #DA291C, Gris #A7A8AA, Azul #003DA5
- Dominio autorizado: `una.ac.cr`
- Plan básico: 100 análisis/mes con barra de progreso y bloqueo suave
- Reportes Word con identidad institucional

---

## Decisiones de Arquitectura

| Decisión | Opción elegida | Razón |
|---|---|---|
| Output LLM | JSON estructurado (Pydantic + Structured Outputs) | Elimina keyword matching frágil |
| Grammar checker | Reemplazado por estilo académico APA 7 | Grammarly cubre gramática mecánica; nosotros cubrimos lo que Grammarly no hace |
| Coherencia semántica | Descartada | No funciona con adelantos parciales — caso de uso real del piloto |
| RAG multitenant | Índice único compartido (FAISS → pgvector futuro) | El manual APA 7 es universal |
| Aislamiento de datos | Row Level Security en Supabase | Estándar SaaS, sin schemas separados |
| Autenticación | Supabase Auth OTP por dominio | Sin contraseñas propias, sin integración con IdP de cada institución |
| Distribución inicial | App independiente (sin LMS) | Menor fricción para el piloto |
| Feature flags | `config/features.py` cargado desde env/Secrets | Activan módulos por institución sin deploy |

---

## Fase 12 — Dashboard BI Institucional *(pendiente — diseñar con datos reales del piloto)*

> Esta fase va después de 3 meses de piloto para diseñar visualizaciones con datos reales.

### 12.1 — Panel de Control

- Autenticación por rol: `director`, `decano`, `bibliotecario`
- KPIs: total documentos revisados, puntaje APA promedio, top 5 errores, evolución mensual

### 12.2 — Filtros Avanzados

| Filtro | Opciones |
|---|---|
| Facultad / Departamento | Lista dinámica desde BD |
| Período | Mes, semestre, año académico |
| Tipo de documento | Tesis, artículo, ensayo, monografía |
| Nivel | Pregrado, posgrado, doctorado |

### 12.3 — Reportes de Tendencias

- Gráficos de evolución de errores por mes
- Comparativa antes/después de talleres de biblioteca
- Exportación PDF o Excel

**Stack:** `plotly` + `pandas` + `streamlit-authenticator`

---

## Fase 13 — Expansión Comercial *(post-piloto)*

- Caso de estudio publicado con datos del piloto (PDF 8-12 páginas)
- Migración RAG de FAISS a pgvector (Supabase)
- Integración Moodle (LTI)
- Panel Superadmin para gestión de instituciones y cuotas
- Dataset público "Errores_APA_Latam" (Hugging Face / Zenodo)

---

## Cronograma

```
2026
 Mar - Abr  │ Fases 0–11  │ Producto base + infraestructura SaaS + piloto UNA ✅
 May - Jul  │ Fase 11     │ Piloto activo — recolección de datos reales (3 meses)
 Ago - Sep  │ Fase 12     │ Dashboard BI con datos del piloto
 Oct        │ Fase 13     │ Caso de estudio + expansión a nuevas instituciones
```

---

*Documento vivo — actualizar al completar cada fase.*
*Autor: Michael González · Proyecto: Agente APA 7 · © 2026*
