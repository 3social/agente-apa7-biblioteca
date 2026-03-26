# Agente APA7 — Guía General de Contexto

**Proyecto**: Plataforma SaaS para revisión académica APA 7 en Latinoamérica  
**Stack**: Python + FastAPI + OpenAI GPT-4o-mini + Pydantic v2 + Supabase  
**Piloto Activo**: Universidad Nacional de Costa Rica (UNA)  
**Estado**: Operativo (Fases 0-11 completadas)

---

## Arquitectura en 30 Segundos

```
Flujo: .docx → engine.py → [apa_validator + academic_style + analytics] → Supabase

Componentes Principales:
├── core/engine.py              Orquestador central (sin UI)
├── modules/
│   ├── apa_validator.py        Análisis APA con LLM (Structured Outputs)
│   ├── academic_style.py       Detección de estilo académico (E01-E06)
│   ├── analytics.py            Escritura a Supabase multitenant
│   ├── citation_extractor.py   Extracción de secciones del .docx
│   ├── document_formatter.py   Validación formato sin LLM
│   └── [otros módulos]
├── rag/knowledge_base.py       RAG sobre Manual APA 7 (FAISS → pgvector)
├── api/main.py                 REST API (FastAPI)
├── config/
│   ├── settings.py             Vars de entorno
│   ├── features.py             Feature flags (E01-E06, formato, etc.)
│   └── branding.py             Identidad institucional
└── supabase/                   Migraciones SQL (multitenant + RLS)
```

---

## Los 3 Módulos Más Editados

| Archivo | Líneas | Propósito | Edita Aquí Para | 
|---------|--------|-----------|---|
| `apa_validator.py` | ~150 | Core LLM | Mejorar detección APA, ajustar SYSTEM_PROMPT |
| `academic_style.py` | ~200 | Estilo (E01-E06) | Refinar categorías de estilo |
| `analytics.py` | ~120 | Supabase persistence | Mapear campos, error handling |

**LEE PRIMERO**: `CLAUDE-[nombre].md` en la carpeta `modules/` antes de editar cada uno.

---

## Antes de Cada Sesión en VS Code

1. ✅ **Identifica QUÉ módulo vas a editar** (apa_validator, academic_style, o analytics)
2. ✅ **Abre `modules/CLAUDE-[nombre].md`** — contexto específico para ese módulo
3. ✅ **Lee la sección "Cambios Comunes"** — sugiere 3-5 patrones típicos
4. ✅ **Copia el patrón de prompt** que más se acerca a tu cambio
5. ✅ **Pega en Claude Extension** + personaliza
6. ✅ **NO cargues el archivo completo** — usa los contextos de la guía
7. ✅ **Test local**: `pytest tests/` antes de git commit

---

## Flujo de Análisis (Para Contexto)

```
Usuario sube .docx
    ↓
engine.py: analizar_documento(DocumentoAPA, contexto_RAG)
    ├── apa_validator.py
    │   └── LLM analiza: citas huérfanas, referencias, formato APA
    │   └── Retorna: AnalisisAPA tipado (Structured Outputs)
    │
    ├── document_formatter.py (opcional, flag)
    │   └── Validación física: fuente, márgenes, interlineado, sangría
    │
    ├── academic_style.py (opcional, flag)
    │   └── LLM analiza: E01-E06 (sesgo, registro, primera persona, etc.)
    │   └── Retorna: AnalisisEstilo tipado
    │
    └── analytics.py
        └── Escribe en Supabase: documents + apa_errors (con service_role key)
```

---

## Schemas (Contratos Entre Módulos)

**NO MODIFICAR SIN COORDINAR**:

```python
# DocumentoAPA (salida de citation_extractor → entrada a análisis)
class DocumentoAPA(BaseModel):
    portada: str | None
    abstract: str | None
    cuerpo: str | None
    referencias: str | None
    tablas: list[str] = []
    figuras: list[str] = []
    apendices: str | None
    encabezados: list[Encabezado] = []

# AnalisisAPA (salida de apa_validator → entrada a analytics)
class AnalisisAPA(BaseModel):
    feedback_texto: str                    # Markdown
    errores: list[ErrorAPA]               # Tipado
    puntaje_apa: int                       # 0-100
    resumen: ResumenAnalisis
    errores_formato: int | None
    errores_estilo: int | None

# AnalisisEstilo (salida de academic_style)
class AnalisisEstilo(BaseModel):
    errores: list[ErrorEstilo]            # E01-E06
    observacion: str                       # Feedback general
```

Si necesitas añadir campos: **pregunta primero en la guía del módulo**.

---

## Dependencias Externas

| Librería | Función | Dónde |
|----------|---------|-------|
| `openai` | LLM analysis | apa_validator, academic_style |
| `langchain` + `faiss-cpu` | RAG knowledge base | rag/knowledge_base.py |
| `supabase` | Multitenant BD | analytics.py |
| `pydantic` v2 | Validación de tipos | modules/schemas.py |
| `python-docx` | Extracción .docx | modules/citation_extractor.py |
| `fastapi` | REST API | api/main.py |

---

## Feature Flags (En config/features.py)

| Flag | Default | Qué Activa |
|------|---------|-----------|
| `FEATURE_VALIDACION_CITAS` | `true` | Core apa_validator (siempre activo) |
| `FEATURE_EXTRACTOR_COMPLETO` | `false` | Extracción de todas las secciones |
| `FEATURE_VALIDACION_FORMATO` | `false` | document_formatter.py |
| `FEATURE_ESTILO_ACADEMICO` | `false` | academic_style.py (E01-E06) |

Configurar en `.env` (local) o Streamlit Secrets (nube).

---

## Stack Rápido

```
Frontend:  Streamlit (app.py) — cliente del Core Engine
Backend:   Core desacoplado (core/engine.py) + FastAPI REST
IA:        OpenAI GPT-4o-mini (Structured Outputs para schema válido)
RAG:       LangChain + FAISS sobre Manual APA 7
BD:        Supabase (PostgreSQL + RLS + pgvector habilitado)
Auth:      OTP por dominio universitario (Supabase Auth)
```

---

## Limitaciones Globales (Respetadas)

- ✋ **Máximo 8,000 caracteres por sección** para el contexto LLM (controlar tokens)
- ✋ **Máximo 6,000 caracteres del cuerpo** en apa_validator (6_000 = _MAX_CUERPO)
- ✋ **Máximo 500 caracteres de contexto RAG** por sección (_MAX_CONTEXTO)
- ✋ **No cambiar nombres de tabla en Supabase** (documents, apa_errors)
- ✋ **No modificar esquemas Pydantic sin coordinar** inter-módulos

---

## Próximos Pasos (Como Usuario)

### Para Editar apa_validator.py:
Abre: `modules/CLAUDE-apa-validator.md`

### Para Editar academic_style.py:
Abre: `modules/CLAUDE-academic-style.md`

### Para Editar analytics.py:
Abre: `modules/CLAUDE-analytics.md`

Cada guía tiene:
- Estructura del módulo
- Cambios comunes con patrones de prompt
- Esquema de salida (no modificar)
- Checklist de verificación

---

## Workflow Recomendado

```
1. Abro VS Code → VS Code Claude Extension
2. Abre modules/CLAUDE-[nombre].md
3. Identifica el cambio que quieres hacer
4. Copia el "Patrón de Prompt" más cercano
5. Pega en Claude Extension + personaliza
6. Claude genera el código
7. Copias el output → reemplazas en el archivo
8. Cierras VS Code
9. Terminal: pytest tests/ (verifica que sigue andando)
10. Si pasa: git commit -m "..."
11. Si falla: nueva sesión Claude con el error
```

**Clave**: Una sesión = un cambio en un módulo. **NO mezcles módulos en la misma sesión.**

---

## Cuándo Escalar

Algunos cambios necesitan **contexto cross-módulo** → mejor en **Agente APA7 (Juntiva)**:

- Rediseño del flujo engine.py (afecta todos los módulos)
- Migración FAISS → pgvector (arquitectura RAG)
- Integración Moodle LTI (componente nuevo)
- Dashboard BI institucional (Fase 12)

Para cambios locales a un módulo: **VS Code + Claude Extension + las guías aquí**.

---

*Documento vivo — actualizar conforme avance el proyecto.*  
*Autor: Michael González · © 2026*
