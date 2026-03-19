# Roadmap de Evolución: De Prototipo a SaaS Académico
### Agente APA 7 — Plataforma Institucional de Revisión Académica

> **Objetivo estratégico:** Transformar el validador APA 7 en una plataforma SaaS multi-institución,
> escalable, con analítica de datos y arquitectura desacoplada lista para integraciones móviles y web.

---

## Estado Actual (Línea Base)

| Componente | Estado | Limitación conocida |
|---|---|---|
| Validador APA 7 con IA (GPT-4o-mini) | Operativo | Solo valida cuerpo + referencias |
| RAG sobre Manual APA 7 (FAISS en memoria) | Operativo | No persiste, no escala en multi-instancia |
| Analítica básica en Supabase (tabla única) | Operativo | Detección por keyword matching frágil |
| Interfaz Streamlit | Operativo | Acoplada al motor de análisis |
| Generación de reportes Word | Operativo | Sin marca institucional |

---

> ## Orden de ejecución real
> El piloto con la universidad ya está confirmado.
> El riesgo principal no es la arquitectura SaaS — es llegar al piloto con un producto incompleto.
> **Primero se completa el producto base. Luego se construye la infraestructura SaaS.**

---

## Fase 0 — Producto Base Completo *(Prioridad máxima — antes que todo)*
**Completar el motor de revisión antes del piloto**

El sistema actual solo extrae cuerpo y referencias buscando encabezados por nombre. Un documento
APA 7 real incluye portada, resumen, jerarquía de encabezados, tablas, figuras y apéndices.
Esta fase cierra ese gap con tres módulos nuevos y una reestructuración del output del LLM.

---

### 0.1 — Output estructurado del LLM *(cambio arquitectural base)*

Hoy el LLM devuelve texto libre. El analytics lo procesa con keyword matching (`"huérfana" in feedback`),
lo cual es frágil: si el modelo cambia su redacción, los datos se corrompen silenciosamente.

**Solución:** El LLM devuelve siempre un JSON estructurado más el texto de feedback para el alumno.

```json
{
  "feedback_texto": "...(markdown legible para el alumno)...",
  "errores": [
    {
      "tipo": "cita_huerfana",
      "severidad": "alta",
      "fragmento": "García, 2021",
      "regla_apa": "Sección 8.11",
      "sugerencia": "Agregar la referencia completa al listado final."
    }
  ],
  "puntaje_apa": 72,
  "resumen": {
    "total_errores": 5,
    "errores_criticos": 2,
    "errores_menores": 3
  }
}
```

**Impacto:** Elimina el keyword matching. Es la base del esquema de datos de Supabase y del
dashboard de analítica. Sin esto, las Fases siguientes no tienen cimientos.

**Implementación:** `response_format={"type": "json_object"}` en la llamada a OpenAI +
modelo Pydantic para validar el schema de respuesta.

---

### 0.2 — Módulo de Formato Físico (`modules/document_formatter.py`)

Valida que el documento cumpla las reglas de presentación APA 7. **No usa LLM** — son reglas
deterministas aplicadas sobre las propiedades del `.docx`. Rápido, sin costo de tokens.

**Qué valida:**

| Elemento | Regla APA 7 |
|---|---|
| Fuente | Times New Roman 12pt o Calibri 11pt |
| Interlineado | Doble en todo el documento |
| Márgenes | 2.54 cm en los cuatro lados |
| Sangría | 1.27 cm en primera línea de cada párrafo |
| Portada | Título, autor, institución, curso, fecha |
| Encabezados | Jerarquía H1–H5 con estilos correctos |
| Numeración | Página en esquina superior derecha |
| Tablas y figuras | Etiqueta, título y nota en formato APA |

**Stack:** `python-docx` puro. Reglas configurables en `config/apa_rules.py`.

**Output:** Lista de incumplimientos de formato integrada en el JSON estructurado de 0.1.

---

### 0.3 — Módulo de Coherencia Semántica (`modules/semantic_analyzer.py`)

Analiza si el contenido del documento es internamente coherente como trabajo académico.
Complementa la validación APA (que es formal) con una lectura de fondo del texto.

**Qué evalúa:**

| Categoría | Detalle |
|---|---|
| Coherencia argumental | Las ideas del cuerpo sostienen la tesis declarada |
| Consistencia temática | No hay saltos temáticos abruptos sin transición |
| Relación intro–conclusión | Las conclusiones responden a los objetivos planteados |
| Uso de fuentes | Las citas refuerzan los argumentos, no son decorativas |

**Stack:** LLM (GPT-4o-mini) con prompt especializado en análisis estructural de textos académicos.
Output integrado en el JSON estructurado de 0.1 como campo `"coherencia_semantica"`.

---

### 0.4 — Módulo de Gramática Académica (`modules/grammar_checker.py`)

Detecta problemas de lenguaje que afectan la calidad formal de un trabajo universitario.

**Qué detecta:**

| Categoría | Ejemplos |
|---|---|
| Vicios de lenguaje | Queísmo, dequeísmo, cosismo, laísmo |
| Concordancia | Género, número, tiempos verbales inconsistentes |
| Tono formal | Primera persona, coloquialismos, imprecisión léxica |
| Ortografía técnica | Términos científicos, siglas, extranjerismos |

**Stack:** LLM con prompt especializado. No se usa `language-tool-python` (requiere Java,
difícil de deployar) ni spaCy (no entiende tono académico latinoamericano en contexto).
El costo de una llamada adicional es mínimo y la calidad es muy superior.

**Output:** Campo `"gramatica"` en el JSON estructurado de 0.1.

---

### 0.5 — Extractor completo de secciones (`modules/citation_extractor.py`)

Refactorizar el extractor actual para reconocer todas las secciones de un documento APA 7,
no solo el cuerpo y las referencias.

**Secciones a reconocer:**

```
Portada → Resumen / Abstract → Cuerpo (con encabezados H1–H5)
→ Referencias → Apéndices → Tablas y Figuras
```

**Resultado al completar la Fase 0:**
El sistema puede revisar un documento APA 7 completo en todos sus niveles:
formato físico, gramática académica, coherencia argumental y normas de citación.
Este es el producto que va al piloto.

---

## Fase 9 — Desacoplamiento y API-fication
**Arquitectura Core — Independencia de Streamlit**

**Objetivo:** Separar el motor de análisis de la capa visual, permitiendo conectar en el futuro
una App Móvil, una Web en React, o cualquier cliente externo.

### 9.1 — Core Engine (`core/engine.py`)

- Refactorizar todos los módulos para que funcionen sin dependencias de `st.*` (Streamlit).
- Crear `core/engine.py` como orquestador del flujo completo de análisis.
- El engine recibe bytes del `.docx` y devuelve el JSON estructurado — sin saber nada de la UI.

### 9.2 — API REST (FastAPI)

Exponer el engine como API interna:

| Endpoint | Método | Descripción |
|---|---|---|
| `/analyze` | POST | Recibe `.docx`, retorna JSON de análisis completo |
| `/metrics/{university_id}` | GET | Métricas institucionales filtradas por tenant |
| `/universities` | GET/POST | Gestión de instituciones (solo superadmin) |

**Streamlit pasa a ser un cliente más** de esta API, igual que podría serlo una app móvil.

---

## Fase 10 — Ingeniería de Datos Pro con Supabase
**Estructura SaaS · Multitenant · RAG Persistente**

### 10.1 — RAG Persistente con pgvector

**Problema actual:** FAISS se construye en memoria en cada arranque. No escala en multi-instancia
ni en multi-tenant.

**Solución:** Migrar a **pgvector en Supabase** (ya disponible, sin infraestructura nueva).
El índice vectorial del manual APA 7 se construye **una sola vez** y es compartido por todas
las universidades. Un tenant no tiene su propio índice — el manual es universal.

**Beneficio:** Cero costo de embeddings por sesión. El índice persiste entre deployments.

---

### 10.2 — Esquema Relacional Multitenant

```sql
-- Universidades (tenants)
universities (
  id UUID PRIMARY KEY,
  name TEXT,
  country TEXT,
  authorized_domains TEXT[],   -- ej: ["ucr.ac.cr", "ucr.edu"]
  plan_tier TEXT,              -- "basico" | "profesional" | "institucional"
  logo_url TEXT,
  primary_color TEXT,
  active BOOLEAN,
  created_at TIMESTAMPTZ
)

-- Documentos analizados
documents (
  id UUID PRIMARY KEY,
  university_id UUID REFERENCES universities(id),
  filename TEXT,
  uploaded_at TIMESTAMPTZ,
  word_count INTEGER,
  student_code TEXT,           -- anonimizado
  puntaje_apa INTEGER
)

-- Errores APA detectados (tipificados desde el JSON estructurado)
apa_errors (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  tipo TEXT,                   -- "cita_huerfana" | "formato_sangria" | etc.
  severidad TEXT,              -- "alta" | "media" | "baja"
  regla_apa TEXT,              -- "Sección 8.11"
  sugerencia TEXT
)

-- Errores de gramática
grammar_errors (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  categoria TEXT,              -- "vicio_lenguaje" | "concordancia" | "tono"
  fragmento TEXT,
  sugerencia TEXT
)
```

**Aislamiento de datos:** Row Level Security (RLS) en Supabase con `university_id` en el JWT.
Un tenant nunca accede a datos de otro. Una política, aplicada automáticamente a todas las consultas.
Se descarta el enfoque de schemas separados por cliente — la complejidad operativa no lo justifica.

---

### 10.3 — Autenticación por Dominio Universitario

**Flujo de acceso:**

```
Superadmin registra universidad
  └── Define dominios autorizados (ej: @ucr.ac.cr)
      └── Alumno/Bibliotecario entra con email institucional
          └── Supabase Auth verifica el dominio → acceso concedido al tenant correcto
```

**Stack:** Supabase Auth + Magic Link o Google OAuth. Sin contraseñas que gestionar.
Sin integración compleja con el IdP de cada universidad. Funciona desde el día 1.

---

### 10.4 — Panel Superadmin

Interfaz exclusiva del operador de la plataforma (tú). Mínimo viable:

- Alta de universidades (nombre, dominio, plan)
- Ver uso por institución (documentos analizados / cuota)
- Activar y desactivar cuentas
- Monitor de errores del sistema en producción

Implementación inicial: ruta protegida en Streamlit. Migrable a panel dedicado en fases posteriores.

---

### 10.5 — Dataset "Errores_APA_Latam"

Recolección anónima y ética de datos para construir el primer dataset público de tendencias
de escritura académica en América Latina.

**Principios:**
- Anonimización automática — ningún dato permite identificar al alumno.
- Opt-in institucional — cada universidad autoriza la contribución al dataset.
- Licencia abierta para la comunidad investigadora (CC BY 4.0).

**Variables a capturar:** tipo de error más frecuente por país, proporción de errores de citación
vs. formato vs. gramática, evolución temporal por semestre.

**Publicación objetivo:** Hugging Face o Zenodo, posicionando el proyecto como referente
regional en escritura académica.

---

## Fase 11 — Piloto con Universidad Real *(adelantada — ya hay institución confirmada)*
**Go-to-Market · Validación · Caso de Estudio**

> Esta fase se adelanta porque ya existe una universidad dispuesta.
> Los datos del piloto informan el diseño del Dashboard BI (Fase 12).

### 11.1 — White Label

- Configuración por universidad: logo, colores, nombre institucional.
- Parámetros cargados desde `universities` en Supabase.
- Reportes Word generados con la marca de la institución.
- Implementación: `config/branding.py`.

### 11.2 — Gestión de Cuotas (SaaS Billing Ready)

| Plan | Análisis/mes | Usuarios | Soporte |
|---|---|---|---|
| Básico | 100 | 1 biblioteca | Email |
| Profesional | 500 | 5 facultades | Prioritario |
| Institucional | Ilimitado | Campus completo | Dedicado |

- Contador de uso por `university_id` en Supabase.
- Bloqueo suave al alcanzar el límite (notificación, no corte abrupto).
- Preparación de webhooks para integración futura con pasarelas de pago.

### 11.3 — Caso de Estudio (3 meses)

**Métricas a documentar:**

| Métrica | Cómo medirla |
|---|---|
| Trabajos revisados y tiempo ahorrado | Registros en `documents` vs. estimado manual |
| Reducción de errores en el semestre | Puntaje APA promedio mes 1 vs. mes 3 |
| Errores más frecuentes de la institución | Consulta sobre `apa_errors` |
| Satisfacción del bibliotecario | Encuesta NPS al cierre |

**Entregable:** Documento PDF (8–12 páginas) con resultados reales, usable como material
de ventas para nuevas instituciones.

---

## Fase 12 — Dashboard de Inteligencia Institucional (BI)
**Diseñado con datos reales del piloto**

> Esta fase va después del piloto porque los datos reales de la Fase 11 permiten diseñar
> visualizaciones que reflejen lo que los directores realmente necesitan ver.

### 12.1 — Panel de Control para Directores y Decanos

- Módulo Streamlit separado con autenticación por rol (`director`, `decano`, `bibliotecario`).
- KPIs en pantalla principal:
  - Total de trabajos revisados en el período.
  - Puntaje APA promedio de la institución.
  - Top 5 errores más frecuentes.
  - Evolución del puntaje promedio por mes.

### 12.2 — Filtros Avanzados

| Filtro | Opciones |
|---|---|
| Facultad / Departamento | Lista dinámica desde BD |
| Período | Mes, semestre, año académico |
| Tipo de documento | Tesis, artículo, ensayo, monografía |
| Nivel | Pregrado, posgrado, doctorado |

### 12.3 — Reportes de Tendencias

- Gráficos de línea: evolución de errores promedio por mes.
- Comparativa antes/después de talleres de biblioteca.
- Exportación en PDF o Excel para presentaciones institucionales.

**Stack:** `plotly` + `pandas` + `streamlit-authenticator`.

---

## Cronograma Realista

```
2026
 Mar - Abr  │ Fase 0  │ Producto base completo
            │         │  ├── document_formatter.py
            │         │  ├── semantic_analyzer.py
            │         │  ├── grammar_checker.py
            │         │  ├── citation_extractor.py (completo)
            │         │  └── Output JSON estructurado del LLM

 May        │ Fase 9  │ Desacoplamiento: core engine + FastAPI

 Jun        │ Fase 10 │ Infraestructura SaaS
            │         │  ├── pgvector (RAG persistente)
            │         │  ├── Esquema multitenant + RLS
            │         │  ├── Supabase Auth por dominio
            │         │  └── Panel Superadmin

 Jul - Sep  │ Fase 11 │ Piloto con universidad real (3 meses)
            │         │  ├── White label activo
            │         │  └── Recolección de datos reales

 Oct - Nov  │ Fase 12 │ Dashboard BI (con datos del piloto)
            │         │  └── Publicación caso de estudio

 Dic        │         │ Expansión comercial a nuevas instituciones
```

---

## Dependencias Técnicas por Fase

| Fase | Nuevas dependencias |
|---|---|
| 0 | `pydantic` (validación JSON), mejoras en `python-docx` |
| 9 | `fastapi`, `uvicorn` |
| 10 | `pgvector` (extensión Supabase), `supabase-py` actualizado, `streamlit-authenticator` |
| 12 | `plotly`, `pandas` |

---

## Criterios de Aceptación por Fase

| Fase | Criterio |
|---|---|
| 0 | El sistema analiza portada, resumen, cuerpo, referencias y apéndices. El LLM devuelve JSON válido en el 100% de los casos. |
| 9 | El motor de análisis funciona sin importar Streamlit. La API responde correctamente desde un cliente externo. |
| 10 | 3 universidades de prueba con datos completamente aislados. Un alumno de universidad A no puede ver datos de universidad B. |
| 11 | Al menos 100 documentos analizados en producción. Un director genera un reporte de tendencias con datos reales. |
| 12 | Al menos 1 institución paga al finalizar el piloto. Caso de estudio publicado. |

---

## Decisiones de Arquitectura Confirmadas

| Decisión | Opción elegida | Razón |
|---|---|---|
| RAG multitenant | Índice único compartido (pgvector) | El manual APA 7 es universal. Sin costo de embeddings por tenant. |
| Output del LLM | JSON estructurado + texto markdown | Base del analytics tipificado. Elimina keyword matching frágil. |
| Grammar checker | LLM con prompt especializado | Mejor calidad en español académico latinoamericano. Sin dependencias Java. |
| Aislamiento de datos | Row Level Security en Supabase | Estándar de industria para SaaS en Supabase. Menor complejidad operativa que schemas separados. |
| Autenticación | Supabase Auth + dominio universitario | Sin contraseñas propias. Sin integración con IdP de cada institución. |
| Distribución inicial | App independiente (sin LMS) | Menor fricción para arrancar. Integración con Moodle es una fase posterior. |

---

*Documento vivo — actualizar al completar cada fase.*
*Autor: Michael González · Proyecto: Agente APA 7 · © 2026*
