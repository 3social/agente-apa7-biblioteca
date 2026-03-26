# academic_style.py — Detección de Estilo Académico APA 7

**Responsabilidad**: `DocumentoAPA` (tipado) → `AnalisisEstilo` (tipado)  
**Detecta**: 6 categorías de estilo académico (E01-E06)  
**Líneas**: ~200 | **Cambios Frecuentes**: SYSTEM_PROMPT, categorías E01-E06, ejemplos

---

## Estructura

```python
_PROMPT_SISTEMA               # Instrucciones al LLM (EDITA AQUÍ)
_MAX_CUERPO = 5_000          # Límite cuerpo redactado
_MAX_SECCION = 400           # Límite abstract/apéndices

_construir_texto()           # Extrae abstract + cuerpo + apéndices
analizar_estilo()            # FUNCIÓN PRINCIPAL — orquestadora
```

---

## Las 6 Categorías (NO cambiar códigos)

| ID | Categoría | Descripción | Ejemplo |
|-------|-----------|-------------|---------|
| **E01** | Lenguaje con sesgo | Terminología que estigmatiza por identidad | ❌ "los discapacitados" → ✅ "personas con discapacidad" |
| **E02** | Registro informal | Coloquialismos, jerga, habla cotidiana | ❌ "la cosa es que", "un montón de" → ✅ Lenguaje formal |
| **E03** | Primera persona inapropiada | "Yo creo" sin respaldo empírico | ❌ "yo creo que..." → ✅ "Los datos muestran..." |
| **E04** | Afirmaciones sin respaldo | Generalizaciones sin cita | ❌ "está comprobado que" → ✅ "(Author, YYYY) encontró que..." |
| **E05** | Verbosidad y redundancia | Frases que repiten innecesariamente | ❌ "a través del uso de la utilización de" → ✅ "usando" |
| **E06** | Voz pasiva excesiva | Cuando hay alternativa activa clara | ❌ "fue analizado por..." → ✅ "analizamos..." |

---

## Flujo Interno

```
analizar_estilo(documento: DocumentoAPA, api_key: str)
    ↓
_construir_texto() → extrae abstract + cuerpo + apéndices (máx 5K+400)
    ↓
Llamada a OpenAI:
  client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": _PROMPT_SISTEMA},
      {"role": "user", "content": f"--- TEXTO DEL TRABAJO ---\n{texto}"},
    ],
    response_format=AnalisisEstilo,  ← Structured Outputs
    temperature=0.2,
  )
    ↓
Retorna: AnalisisEstilo (tipado, garantizado válido)
```

---

## SYSTEM_PROMPT Actual (Resumen)

El string `_PROMPT_SISTEMA` tiene estas secciones:

1. **Rol**: "Experto en escritura académica latinoamericana + APA 7..."
2. **Tarea**: Analizar SOLO estilo académico, no gramática mecánica
3. **6 Categorías** (E01-E06) con ejemplos
4. **Reglas**:
   - Máximo 10 errores
   - Tono pedagógico
   - Si sin problemas → lista vacía + observación positiva

**Tono**: Constructivo, nunca punitivo.

---

## 3 Cambios Comunes (Con Patrones)

### Cambio 1: Mejorar Detección de E03 (Primera Persona)

**Por qué**: Estudiantes escriben "nosotros analizamos" en un trabajo individual.

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/academic_style.py
LECTURA PREVIA: Leído CLAUDE-academic-style.md

CAMBIO: Refinar detección de E03 (primera persona inapropiada)

CONTEXTO ACTUAL:
[Copia la sección del SYSTEM_PROMPT sobre E03 (líneas ~40-50)]

PROBLEMA:
Los estudiantes escriben "nosotros analizamos" en adelantos individuales.
El LLM debería detectar cuándo "nosotros" o "yo" se usa en contexto donde
debería ser impersonal (descripción de métodos, resultados).

MEJORA PEDIDA:
En SYSTEM_PROMPT, sección E03, añade:
"E03 PROBLEMA REAL: Uso de primera persona para hacer afirmaciones no sustentadas
('yo creo que', 'en mi opinión', 'me parece que') SIN respaldo empírico.
También detectar: en trabajos individuales, uso de 'nosotros' cuando debería ser singular.
En descripciones de métodos, impersonal excesivo ('el investigador procede a...') 
cuando se debería usar 'yo' o 'nosotros'."

SALIDA:
El SYSTEM_PROMPT completo (variable `_PROMPT_SISTEMA`) con la mejora.
```

**Lo que esperas recibir**: El string `_PROMPT_SISTEMA` completo, mejorado.

---

### Cambio 2: Añadir Nueva Categoría de Estilo (Raro, pero posible)

**Por qué**: Descubriste un patrón nuevo que los estudiantes cometen (ej: "citas sin introducción").

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/academic_style.py
LECTURA PREVIA: Leído CLAUDE-academic-style.md

CAMBIO: Añadir categoría E07 (nuevo patrón de estilo)

PROBLEMA:
Los estudiantes insertan citas sin introducción: "La ciencia es importante 
(Author, 2020)." Debería ser: "Según Author (2020), la ciencia es importante."

NUEVA CATEGORÍA:
E07 - Citas sin introducción: Cita aparecesin contexto, no se explica su relevancia.

PATRÓN DE PROMPT:
En SYSTEM_PROMPT, después de E06, añade sección E07 con:
- Definición clara
- 2 ejemplos (incorrecto + correcto)
- Cuándo flagear (solo cuando hay alternativa clara)

SALIDA:
El SYSTEM_PROMPT completo con la nueva E07 integrada.

ADVERTENCIA:
Después, coordiná con analytics.py para mapear el nuevo tipo en `ErrorEstilo.tipo`.
```

**Lo que esperas recibir**: SYSTEM_PROMPT con E07.

---

### Cambio 3: Ajustar Límites de Caracteres

**Por qué**: OpenAI rechaza "contexto muy largo".

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/academic_style.py
LECTURA PREVIA: Leído CLAUDE-academic-style.md

CAMBIO: Reducir límites de caracteres

PROBLEMA:
OpenAI retorna LengthFinishReasonError → el texto es demasiado largo.

SOLUCIÓN PEDIDA:
Reduce:
  _MAX_CUERPO de 5_000 a 3_000
  _MAX_SECCION de 400 a 250

SALIDA:
Solo las 3 líneas con los nuevos valores.
```

**Lo que esperas recibir**: 3 líneas con los nuevos valores.

---

## Schema de Salida (NO MODIFICAR)

```python
class ErrorEstilo(BaseModel):
    id: Literal['E01', 'E02', 'E03', 'E04', 'E05', 'E06']  # NO añadir E07+ sin coordinar
    severidad: Literal['alta', 'media', 'baja']
    fragmento: str                                          # Texto exacto
    sugerencia: str                                         # Cómo mejorar
    explicacion: str                                        # Por qué es un problema

class AnalisisEstilo(BaseModel):
    errores: list[ErrorEstilo]          # Máximo 10
    observacion: str                     # Feedback general (positivo si no hay errores)
```

**Contrato**: Este schema es lo que retorna `analizar_estilo()` y lo consume `analytics.py`.

---

## Dependencias

| Módulo | Función |
|--------|---------|
| `schemas.py` | Define `DocumentoAPA`, `AnalisisEstilo`, `ErrorEstilo` |
| `OpenAI API` | `client.beta.chat.completions.parse()` con Structured Outputs |

**NO edites estas dependencias desde aquí.**

---

## Limitaciones (Respetadas)

- ✋ No cambiar IDs de categoría ('E01'-'E06') — son el estándar
- ✋ No cambiar severidades ('alta', 'media', 'baja')
- ✋ No aumentar _MAX_* por encima de 6_000 total (riesgo token overflow)
- ✋ No cambiar modelo (siempre "gpt-4o-mini")
- ✋ Máximo 10 errores por documento
- ✋ Si añades E07+, coordiná antes con analytics.py

---

## Checklist Antes de Pedir Cambios

- [ ] ¿He identificado si es cambio a SYSTEM_PROMPT, límites, o categorías?
- [ ] ¿He leído el SYSTEM_PROMPT actual (líneas ~20-100)?
- [ ] ¿He considerado el impacto en tokens de OpenAI?
- [ ] ¿El schema de salida sigue siendo AnalisisEstilo?
- [ ] ¿Las nuevas instrucciones al LLM son pedagógicas?
- [ ] ¿Si añado E07+, he coordinado con analytics.py?

---

## Flujo de Edición Recomendado

```
1. Leo CLAUDE-academic-style.md (este archivo)
2. Identifico el tipo de cambio (SYSTEM_PROMPT / límites / categorías)
3. Copio el patrón de prompt correspondiente
4. Pego en Claude Extension + personalizo
5. Claude genera el código
6. Copios output → reemplazo en academic_style.py
7. pytest tests/test_academic_style.py --verbose
8. Si pasa: git commit -m "feat(academic_style): [cambio específico]"
```

**CRÍTICO**: Una sesión = UN cambio. No mezcles cambios.

---

## Ejemplos de Cambios Efectivos (Documentados)

*[Se actualiza conforme uses el módulo — patrón que funcionó bien]*

---

*Guía específica para módulo academic_style.py*  
*Última actualización: 2026-03-25*
