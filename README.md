# Agente de Revisión APA 7 - Ecosistema Modular de Biblioteca
> **Plataforma Profesional de Revisión Académica con Arquitectura Modular, IA y RAG.**
> En evolución activa hacia SaaS académico multi-institución.

Este ecosistema automatiza la revisión bibliográfica en bibliotecas universitarias, integrando
Inteligencia Artificial con una Base de Conocimiento propia y un sistema de Analítica Institucional,
bajo una arquitectura modular escalable con feature flags para control de funcionalidades por etapa.

---

## Arquitectura del Sistema

```
APA_Validator/
├── app.py                        # Orquestador principal (Streamlit)
├── config/
│   ├── settings.py               # API Keys y rutas (env / Streamlit Secrets)
│   └── features.py               # Feature flags — control de módulos activos
├── modules/
│   ├── schemas.py                # Contratos de datos (Pydantic): DocumentoAPA, AnalisisAPA
│   ├── citation_extractor.py     # Extractor de secciones del .docx (básico y completo)
│   ├── apa_validator.py          # Motor de análisis APA 7 con Structured Outputs
│   └── analytics.py             # Conector Supabase — analítica institucional
├── rag/
│   └── knowledge_base.py        # RAG sobre Manual APA 7 con queries dirigidas por sección
└── reports/
    └── report_generator.py      # Generación de reportes Word para el alumno
```

---

## Flujo de Análisis

```
.docx subido
    │
    ▼
citation_extractor.py
  ├── Modo básico (default):   cuerpo + referencias
  └── Modo completo (flag):    portada, abstract, cuerpo H1-H5,
                               referencias, apéndices, tablas, figuras
    │
    ▼
knowledge_base.py (RAG)
  └── Queries dirigidas por sección → recupera reglas APA 7 relevantes
      Solo consulta secciones con contenido Y con flag activo
    │
    ▼
apa_validator.py (GPT-4o-mini · Structured Outputs)
  └── Retorna AnalisisAPA (JSON tipado):
      feedback_texto · errores[] · puntaje_apa · resumen
    │
    ├── analytics.py → Supabase (datos estructurados, no keyword matching)
    ├── app.py       → Streamlit (métricas, reporte, errores por severidad)
    └── report_generator.py → Reporte Word descargable
```

---

## Feature Flags

El sistema usa un mecanismo de feature flags para controlar qué módulos están activos
sin tocar código ni hacer un nuevo deploy. Esto permite habilitar funcionalidades
de forma gradual por ambiente o por institución.

| Flag | Default | Descripción |
|---|---|---|
| `FEATURE_VALIDACION_CITAS` | `true` | Core — siempre activo |
| `FEATURE_EXTRACTOR_COMPLETO` | `false` | Extractor de todas las secciones APA 7 |
| `FEATURE_VALIDACION_FORMATO` | `false` | Validación de formato físico (fuente, márgenes, etc.) |
| `FEATURE_REVISION_GRAMATICA` | `false` | Gramática académica (vicios, concordancia, tono) |
| `FEATURE_ANALISIS_SEMANTICO` | `false` | Coherencia argumental del documento |

**Configuración:** agregar la variable al archivo `.env` (local) o a Streamlit Secrets (nube).

```
FEATURE_EXTRACTOR_COMPLETO=true
```

El sidebar de la aplicación muestra en tiempo real qué módulos están activos.

---

## Características Implementadas

**Análisis de citas y referencias**
Detecta citas huérfanas (en texto sin referencia) y referencias sobrantes (en lista sin citar).
Validación cruzada basada en las reglas del Manual APA 7.

**RAG con queries dirigidas por sección**
El Manual APA 7 (PDF completo) está indexado con LangChain + FAISS.
Cada sección del documento (portada, abstract, encabezados, tablas, referencias, apéndices)
tiene su propia query optimizada. Solo se consultan las secciones presentes en el documento
y con su feature flag activo — reduce costo de tokens y ruido en el contexto del LLM.

**Output estructurado (Pydantic + Structured Outputs de OpenAI)**
El LLM retorna siempre un objeto `AnalisisAPA` válido — nunca texto libre sin estructura.
Esto garantiza datos consistentes en Supabase independientemente de cómo el modelo redacte.

**Analítica institucional sin keyword matching**
Los datos se extraen del objeto tipado `AnalisisAPA`, no del texto del feedback.
Puntaje APA, errores críticos, errores menores y tipo más frecuente se persisten con precisión.

**Extractor completo de secciones (flag: `FEATURE_EXTRACTOR_COMPLETO`)**
Máquina de estados que recorre el documento linealmente:
Portada → Abstract → Cuerpo (H1–H5) → Referencias → Apéndices
con detección lateral de títulos de Tablas y Figuras.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend / UI | Streamlit |
| IA — Análisis APA | OpenAI GPT-4o-mini (Structured Outputs) |
| Contratos de datos | Pydantic v2 |
| RAG — Conocimiento | LangChain + FAISS |
| Base de Datos | Supabase (PostgreSQL) |
| Procesamiento .docx | python-docx |
| Indexación PDF | PyPDFLoader (LangChain) |

---

## Configuración

**Variables de entorno requeridas** (`.env` local o Streamlit Secrets en nube):

```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
```

**Variables opcionales** (feature flags, todas en `false` por defecto):

```
FEATURE_EXTRACTOR_COMPLETO=false
FEATURE_VALIDACION_FORMATO=false
FEATURE_REVISION_GRAMATICA=false
FEATURE_ANALISIS_SEMANTICO=false
```

---

## Roadmap

Ver [ROADMAP.md](ROADMAP.md) para el plan completo de evolución hacia SaaS académico.

**Estado actual:** Fase 0 (producto base) — en progreso.

| Fase | Descripción | Estado |
|---|---|---|
| 0.1 | Output JSON estructurado del LLM | Completado |
| 0.2 | Feature flags + RAG por sección + Extractor completo | Completado |
| 0.3 | Validación de formato físico (`document_formatter.py`) | Pendiente |
| 0.4 | Gramática académica (`grammar_checker.py`) | Pendiente |
| 0.5 | Coherencia semántica (`semantic_analyzer.py`) | Pendiente |
| 9 | Desacoplamiento — FastAPI core engine | Pendiente |
| 10 | Infraestructura SaaS multitenant (Supabase) | Pendiente |
| 11 | Piloto con universidad real | Pendiente |
| 12 | Dashboard BI institucional | Pendiente |

---

## Copyright

© 2026 Michael González. All rights reserved.

This software is protected by copyright law.
Unauthorized reproduction or distribution is prohibited.
