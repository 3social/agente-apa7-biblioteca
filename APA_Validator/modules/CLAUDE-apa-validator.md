# apa_validator.py — Análisis APA 7 con LLM

**Responsabilidad**: `DocumentoAPA` (tipado) → `AnalisisAPA` (tipado)  
**Core del Proyecto**: Análisis con GPT-4o-mini + Structured Outputs  
**Líneas**: ~150 | **Cambios Frecuentes**: SYSTEM_PROMPT, límites (_MAX_*), error handling

---

## Estructura

```python
_PROMPT_SISTEMA               # Instrucciones al LLM (EDITA AQUÍ)
_MAX_CUERPO = 6_000          # Límite del cuerpo (6KB)
_MAX_REFS = 2_000            # Límite referencias (2KB)
_MAX_SECCION = 500           # Límite portada/abstract/apéndices
_MAX_CONTEXTO = 500          # Límite contexto RAG por sección

_construir_contexto()        # Formatea dict de reglas APA por sección
_construir_documento()       # Formatea DocumentoAPA para el prompt
analizar_trabajo()           # FUNCIÓN PRINCIPAL — orquestadora
```

---

## Flujo Interno

```
analizar_trabajo(documento: DocumentoAPA, contexto: dict, api_key: str)
    ↓
Construye dos strings:
  1. _construir_contexto(contexto) → "=== REGLAS APA 7: CITAS ===\n..."
  2. _construir_documento(documento) → "PORTADA:\n... CUERPO:\n..."
    ↓
Llamada a OpenAI:
  client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": _PROMPT_SISTEMA},
      {"role": "user", "content": prompt_usuario},
    ],
    response_format=LLMAnalisisAPA,  ← Structured Outputs
    temperature=0.2,
  )
    ↓
Retorna: AnalisisAPA (tipado, garantizado válido)
```

---

## SYSTEM_PROMPT Actual (Resumen)

El string `_PROMPT_SISTEMA` está dividido en 3 partes:

1. **Rol**: "Eres un bibliotecario experto en APA 7..."
2. **Tareas**:
   - COHERENCIA: citas huérfanas + referencias sobrantes
   - FORMATO APA 7: verifica contra manual
   - CORRECCIONES: fragmento exacto + regla + ejemplo correcto
3. **Reglas de Output**:
   - `feedback_texto`: Markdown con secciones
   - `puntaje_apa`: 0-100 (criterios: 90-100 menores, 70-89 formato, etc.)
   - `errores`: Tipificados (tipo: 'coherencia'|'formato_apa', severidad: 'alta'|'media'|'baja')

**Tono**: Constructivo, nunca punitivo.

---

## 3 Cambios Comunes (Con Patrones)

### Cambio 1: Mejorar Detección de Citas Huérfanas

**Por qué**: Estudiantes escriben "(Author, 2020)" en el texto pero no aparece en Referencias.

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/apa_validator.py
LECTURA PREVIA: Leído CLAUDE-apa-validator.md

CAMBIO: Mejorar detección de citas huérfanas (coherencia)

CONTEXTO ACTUAL:
[Copia la línea que dice: "1. COHERENCIA: citas huérfanas..."]

PROBLEMA:
El LLM no siempre detecta patrones como "(Desconocido, s.f.)" o "[sic]".

MEJORA PEDIDA:
En SYSTEM_PROMPT, sección "COHERENCIA", añade esta instrucción:
"Cita huérfana = aparece en texto como (Autor, AÑO) o [cita] pero NO en Referencias.
Casos especiales: (Desconocido, s.f.), [sin date], [comunicación personal].
Reportar cada una en el feedback."

SALIDA:
El SYSTEM_PROMPT completo (variable `_PROMPT_SISTEMA`) con la mejora.
```

**Lo que esperas recibir**: El string `_PROMPT_SISTEMA` completo, mejorado, listo para copiar-pegar.

---

### Cambio 2: Ajustar Límites de Caracteres

**Por qué**: OpenAI rechaza "contexto muy largo" → necesitas reducir _MAX_*.

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/apa_validator.py
LECTURA PREVIA: Leído CLAUDE-apa-validator.md

CAMBIO: Reducir límites de caracteres por tokens

PROBLEMA:
OpenAI retorna LengthFinishReasonError → el documento es demasiado largo.

SOLUCIÓN PEDIDA:
Reduce:
  _MAX_CUERPO de 6_000 a 4_000
  _MAX_CONTEXTO de 500 a 300

SALIDA:
Solo las 5 líneas con los nuevos valores (no todo el código).
```

**Lo que esperas recibir**: 5 líneas con los nuevos valores.

---

### Cambio 3: Mejorar Manejo de Errores en analizar_trabajo()

**Por qué**: Si el LLM rechaza o timeout, quieres reintentar automáticamente.

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/apa_validator.py
LECTURA PREVIA: Leído CLAUDE-apa-validator.md

CAMBIO: Añadir reintento automático en analizar_trabajo()

CONTEXTO ACTUAL:
[Copia la función analizar_trabajo(), líneas ~95-140]

PROBLEMA:
Si LengthFinishReasonError, falla y no reintentas.

MEJORA PEDIDA:
Implementar reintento automático:
1. Primer intento: usa _MAX_CUERPO normal
2. Si LengthFinishReasonError: reduce _MAX_CUERPO en 30%, reintentas
3. Máximo 2 intentos, luego raise ValueError

SALIDA:
La función analizar_trabajo() completa, con reintento implementado.
```

**Lo que esperas recibir**: Función `analizar_trabajo()` completa.

---

## Schema de Salida (NO MODIFICAR)

```python
class ErrorAPA(BaseModel):
    tipo: Literal['coherencia', 'formato_apa']  # NO añadir tipos aquí sin coordinar
    severidad: Literal['alta', 'media', 'baja']
    regla_apa: str                               # "APA 7, p. 342"
    fragmento: str                               # Texto exacto del error
    sugerencia: str                              # Ejemplo de corrección

class ResumenAnalisis(BaseModel):
    total_errores: int
    errores_criticos: int
    errores_menores: int

class AnalisisAPA(BaseModel):
    feedback_texto: str                  # Markdown
    errores: list[ErrorAPA]              # Tipado
    puntaje_apa: int                     # 0-100
    resumen: ResumenAnalisis
    errores_formato: int | None          # Conector a analytics
    errores_estilo: int | None           # Conector a analytics
```

**Contrato**: `analytics.py` depende de esta estructura. Si cambias algo, avisale.

---

## Dependencias

| Módulo | Función |
|--------|---------|
| `schemas.py` | Define `DocumentoAPA`, `AnalisisAPA`, `LLMAnalisisAPA` |
| `knowledge_base.py` | Retorna `dict[str, str]` con contexto RAG por sección |
| `OpenAI API` | `client.beta.chat.completions.parse()` con Structured Outputs |

**NO edites estas dependencias desde aquí.**

---

## Limitaciones (Respetadas)

- ✋ No añadir nuevos tipos de error (`ErrorAPA.tipo`) sin coordinar con schemas.py
- ✋ No cambiar severidades ('alta', 'media', 'baja') — son el estándar
- ✋ No aumentar _MAX_* por encima de 8_000 total (riesgo token overflow)
- ✋ No cambiar modelo (siempre "gpt-4o-mini")
- ✋ No cambiar response_format (siempre LLMAnalisisAPA)
- ✋ No cambiar temperature (0.2 = determinístico)

---

## Checklist Antes de Pedir Cambios

- [ ] ¿He identificado si es cambio a SYSTEM_PROMPT, límites, o error handling?
- [ ] ¿He leído el SYSTEM_PROMPT actual (líneas 15-65)?
- [ ] ¿He considerado el impacto en tokens de OpenAI?
- [ ] ¿El schema de salida sigue siendo AnalisisAPA?
- [ ] ¿Las nuevas instrucciones al LLM son claras y pedagógicas?
- [ ] ¿Sigo retornando int (puntaje_apa 0-100)?

---

## Flujo de Edición Recomendado

```
1. Leo CLAUDE-apa-validator.md (este archivo)
2. Identifico el tipo de cambio (SYSTEM_PROMPT / límites / error handling)
3. Copio el patrón de prompt correspondiente
4. Pego en Claude Extension + personalizo
5. Claude genera el código
6. Copios output → reemplazo en apa_validator.py
7. pytest tests/test_apa_validator.py --verbose
8. Si pasa: git commit -m "feat(apa_validator): [cambio específico]"
```

**CRÍTICO**: Una sesión = UN cambio. No mezcles cambios en la misma sesión.

---

## Ejemplos de Cambios Efectivos (Documentados)

*[Se actualiza conforme uses el módulo — patrón que funcionó bien]*

---

*Guía específica para módulo apa_validator.py*  
*Última actualización: 2026-03-25*
