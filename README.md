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
│   └── quota.py                    # Control de cuotas por plan (básico/profesional/institucional)
├── rag/
│   └── knowledge_base.py           # RAG sobre Manual APA 7 (LangChain + FAISS)
├── reports/
│   └── report_generator.py         # Reporte Word con branding institucional
├── supabase/
│   ├── 001_initial_schema.sql      # Esquema multitenant: universities, documents, apa_errors
│   ├── 002_auth_hooks.sql          # JWT personalizado con university_id (RLS)
│   └── 003_una_pilot.sql           # Datos de la universidad piloto (UNA Costa Rica)
└── static/
    └── logos/                      # Logos institucionales: <university_id>.png
```

---

## Flujo de Análisis

```
Usuario autenticado sube .docx
    │
    ▼
core/engine.py — analizar_documento()
    │
    ├── citation_extractor.py   → Extrae secciones del documento
    │
    ├── knowledge_base.py       → RAG: recupera reglas APA 7 por sección (FAISS)
    │
    ├── document_formatter.py   → Validación de formato físico sin LLM [flag opcional]
    │      F01 Fuente · F02 Márgenes · F03 Interlineado
    │      F04 Sangría · F05 Tamaño página · F06 Numeración
    │
    ├── apa_validator.py        → Análisis citas/referencias con GPT-4o-mini
    │      Retorna AnalisisAPA: feedback · errores[] · puntaje · resumen
    │
    ├── academic_style.py       → Estilo académico APA 7 con LLM [flag opcional]
    │      Sesgo · Registro informal · Primera persona · Afirmaciones sin respaldo
    │
    └── analytics.py            → Supabase: documents + apa_errors (service_role key)
```

---

## Autenticación

Flujo OTP por dominio universitario (sin contraseñas):

```
Email institucional ingresado
    └── Validar dominio contra universities.authorized_domains
          └── Supabase envía código 6 dígitos al email
                └── Usuario ingresa código → sesión activa
                      └── JWT contiene university_id → RLS activo automáticamente
```

---

## Feature Flags

Activan módulos sin tocar código — configurables por institución desde `.env` o Streamlit Secrets.

| Flag | Default | Descripción |
|---|---|---|
| `FEATURE_VALIDACION_CITAS` | `true` | Core — siempre activo |
| `FEATURE_EXTRACTOR_COMPLETO` | `false` | Extractor de todas las secciones APA 7 |
| `FEATURE_VALIDACION_FORMATO` | `false` | Formato físico: fuente, márgenes, interlineado, sangría |
| `FEATURE_ESTILO_ACADEMICO` | `false` | Estilo APA 7: sesgo, registro, primera persona, verbosidad |

---

## Planes y Cuotas

| Plan | Análisis / mes | Descripción |
|---|---|---|
| Básico | 100 | 1 biblioteca |
| Profesional | 500 | Multi-facultad |
| Institucional | Sin límite | Campus completo |

Aviso automático al llegar al 80% del límite. Bloqueo suave al 100%.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend / UI | Streamlit |
| API REST | FastAPI + Uvicorn |
| IA — Análisis APA | OpenAI GPT-4o-mini (Structured Outputs) |
| Contratos de datos | Pydantic v2 |
| RAG — Conocimiento | LangChain + FAISS |
| Base de datos | Supabase (PostgreSQL + RLS) |
| Autenticación | Supabase Auth (OTP por dominio) |
| Procesamiento .docx | python-docx |
| Indexación PDF | PyPDFLoader (LangChain) |

---

## Configuración

**Variables de entorno requeridas** (`.env` local o Streamlit Secrets en nube):

```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...          # Anon key — auth OTP
SUPABASE_SERVICE_KEY=eyJ...  # Service role key — inserts backend
UNIVERSITY_ID=<uuid>         # UUID de la institución activa
```

**Feature flags** (todas en `false` por defecto):

```
FEATURE_EXTRACTOR_COMPLETO=false
FEATURE_VALIDACION_FORMATO=false
FEATURE_ESTILO_ACADEMICO=false
```

**Arrancar la API REST:**

```bash
cd APA_Validator
uvicorn api.main:app --reload --port 8000
```

---

## Estado del Proyecto

| Fase | Descripción | Estado |
|---|---|---|
| 0.1 | Output JSON estructurado del LLM | Completado |
| 0.2 | Feature flags + RAG por sección + Extractor completo | Completado |
| 0.3 | Validación de formato físico (`document_formatter.py`) | Completado |
| 0.4 | Estilo académico APA 7 (`academic_style.py`) | Completado |
| 0.5 | Coherencia semántica | Descartado — no aplica para adelantos parciales |
| 9 | Core Engine desacoplado + FastAPI | Completado |
| 10 | Supabase multitenant: RLS + Auth OTP por dominio | Completado |
| 11 | Piloto UNA Costa Rica: branding + cuotas | Completado |
| 12 | Dashboard BI institucional | Pendiente |

---

## Copyright

© 2026 Michael González. All rights reserved.
This software is protected by copyright law. Unauthorized reproduction or distribution is prohibited.
