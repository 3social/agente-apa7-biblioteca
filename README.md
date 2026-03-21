# Agente de Revisión APA 7
> **Plataforma SaaS académica para bibliotecas universitarias en Latinoamérica.**
> Automatiza la revisión de trabajos académicos con IA, analítica institucional y arquitectura multitenant.

---

## Arquitectura del Sistema

```
APA_Validator/
├── app.py                          # Interfaz Streamlit (cliente del Core Engine)
├── core/
│   └── engine.py                   # Orquestador central — sin dependencias de UI
├── api/
│   └── main.py                     # API REST FastAPI (POST /analyze · GET /health)
├── config/
│   ├── settings.py                 # Variables de entorno (OpenAI, Supabase, branding)
│   ├── features.py                 # Feature flags — activan módulos por institución
│   └── branding.py                 # Identidad visual institucional (logo, colores)
├── modules/
│   ├── schemas.py                  # Contratos Pydantic: DocumentoAPA, AnalisisAPA, ErrorEstilo
│   ├── citation_extractor.py       # Extractor de secciones del .docx
│   ├── apa_validator.py            # Análisis APA 7 con Structured Outputs (GPT-4o-mini)
│   ├── document_formatter.py       # Validación de formato físico sin LLM (python-docx)
│   ├── academic_style.py           # Estilo académico APA 7 (LLM — opcional)
│   ├── analytics.py                # Escritura a Supabase (documents + apa_errors)
│   ├── auth.py                     # Autenticación OTP por dominio universitario
│   └── quota.py                    # Control de cuotas por plan
├── rag/
│   └── knowledge_base.py           # RAG sobre Manual APA 7 (LangChain + FAISS)
├── reports/
│   └── report_generator.py         # Reporte Word con branding institucional
├── supabase/
│   ├── 001_initial_schema.sql      # Esquema multitenant: universities, documents, apa_errors
│   ├── 002_auth_hooks.sql          # JWT personalizado con university_id
│   ├── 003_una_pilot.sql           # Datos piloto: Universidad Nacional de Costa Rica
│   ├── 004_fix_rls_login.sql       # Política pública para validación de dominio en login
│   ├── 005_fix_hook_permissions.sql # Permisos del hook de autenticación
│   └── 006_fix_hook_volatile.sql   # Hook VOLATILE + manejo de excepciones
└── static/
    └── logos/                      # <university_id>.png — logo institucional
```

---

## Flujo de Análisis

```
Usuario autenticado sube .docx
    │
    ▼
core/engine.py — analizar_documento()
    │
    ├── citation_extractor     → Extrae secciones del documento
    ├── knowledge_base (RAG)   → Recupera reglas APA 7 por sección (FAISS)
    ├── document_formatter     → Formato físico sin LLM [flag opcional]
    │     F01 Fuente · F02 Márgenes · F03 Interlineado
    │     F04 Sangría · F05 Tamaño página · F06 Numeración
    ├── apa_validator (LLM)    → Citas y referencias (GPT-4o-mini Structured Outputs)
    ├── academic_style (LLM)   → Estilo académico APA 7 [flag opcional]
    │     Sesgo · Registro informal · Primera persona
    │     Afirmaciones sin respaldo · Verbosidad · Voz pasiva
    └── analytics              → Supabase: documents + apa_errors (service_role)
```

---

## Autenticación

Flujo OTP por dominio universitario — sin contraseñas:

```
Correo institucional ingresado
    └── Validar dominio en universities.authorized_domains
          └── Supabase envía código OTP al correo
                └── Usuario ingresa código → sesión activa
                      └── JWT contiene university_id → RLS activo
```

---

## Feature Flags

Activan módulos sin tocar código — configurables por institución.

| Flag | Default | Descripción |
|---|---|---|
| `FEATURE_VALIDACION_CITAS` | `true` | Core — siempre activo |
| `FEATURE_EXTRACTOR_COMPLETO` | `false` | Extractor de todas las secciones APA 7 |
| `FEATURE_VALIDACION_FORMATO` | `false` | Formato físico: fuente, márgenes, interlineado, sangría |
| `FEATURE_ESTILO_ACADEMICO` | `false` | Estilo APA 7: sesgo, registro, primera persona, verbosidad |

Configurar en `.env` (local) o Streamlit Secrets (nube):
```
FEATURE_VALIDACION_FORMATO=true
```

---

## Planes y Cuotas

| Plan | Análisis / mes | Descripción |
|---|---|---|
| Básico | 100 | 1 biblioteca |
| Profesional | 500 | Multi-facultad |
| Institucional | Sin límite | Campus completo |

Aviso automático al 80% del límite. Bloqueo suave al 100%.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend / UI | Streamlit |
| API REST | FastAPI + Uvicorn |
| IA — Análisis APA | OpenAI GPT-4o-mini (Structured Outputs) |
| Contratos de datos | Pydantic v2 |
| RAG — Conocimiento | LangChain + FAISS |
| Base de datos | Supabase (PostgreSQL + RLS + pgvector habilitado) |
| Autenticación | Supabase Auth — OTP por dominio universitario |
| Procesamiento .docx | python-docx |
| Indexación PDF | PyPDFLoader (LangChain) |

---

## Configuración

**Variables de entorno requeridas** (`.env` o Streamlit Secrets):

```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...            # Anon key — Auth OTP
SUPABASE_SERVICE_KEY=eyJ...    # Service role key — inserts backend
UNIVERSITY_ID=<uuid>           # UUID de la institución activa
```

**Feature flags** (todas en `false` por defecto):

```
FEATURE_EXTRACTOR_COMPLETO=false
FEATURE_VALIDACION_FORMATO=false
FEATURE_ESTILO_ACADEMICO=false
```

**Arrancar la app:**
```bash
cd APA_Validator
streamlit run app.py
```

**Arrancar la API REST (opcional):**
```bash
uvicorn api.main:app --reload --port 8000
```

---

## Estado del Proyecto

| Fase | Descripción | Estado |
|---|---|---|
| 0.1 | Output JSON estructurado del LLM | ✅ Completado |
| 0.2 | Feature flags + RAG por sección + Extractor completo | ✅ Completado |
| 0.3 | Validación de formato físico (`document_formatter.py`) | ✅ Completado |
| 0.4 | Estilo académico APA 7 (`academic_style.py`) | ✅ Completado |
| 0.5 | Coherencia semántica | Descartado |
| 9 | Core Engine desacoplado + FastAPI | ✅ Completado |
| 10 | Supabase multitenant: RLS + Auth OTP por dominio | ✅ Completado |
| 11 | Piloto UNA Costa Rica: branding + cuotas | ✅ Completado |
| 12 | Dashboard BI institucional | Pendiente |

---

## Migraciones Supabase

Ejecutar en orden en **Supabase → SQL Editor**:

| Archivo | Descripción |
|---|---|
| `001_initial_schema.sql` | Tablas base: universities, documents, apa_errors |
| `002_auth_hooks.sql` | Hook JWT + función de dominio |
| `003_una_pilot.sql` | Datos UNA Costa Rica |
| `004_fix_rls_login.sql` | Política pública para login |
| `005_fix_hook_permissions.sql` | Permisos del hook |
| `006_fix_hook_volatile.sql` | Hook robusto con manejo de errores |

---

## Copyright

© 2026 Michael González. All rights reserved.
This software is protected by copyright law. Unauthorized reproduction or distribution is prohibited.
