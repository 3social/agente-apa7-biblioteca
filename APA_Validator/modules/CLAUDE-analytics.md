# analytics.py — Persistencia en Supabase

**Responsabilidad**: Escribe análisis en Supabase (multitenant con RLS)  
**Consume**: `AnalisisAPA` (de apa_validator) + `AnalisisEstilo` (de academic_style)  
**Líneas**: ~120 | **Cambios Frecuentes**: Mapeos de campos, error handling, nuevos tipos de error

---

## Estructura

```python
guardar_metrica_revision()      # FUNCIÓN ÚNICA — orquestadora
  1. Inserta fila en tabla `documents`
  2. Obtiene document_id
  3. Inserta N filas en tabla `apa_errors` (tipificados)
  4. Retorna document_id (o None si falla)
```

---

## Flujo Interno

```
guardar_metrica_revision(
    supabase_url: str | None,
    supabase_key: str | None,
    nombre_archivo: str,
    analisis: AnalisisAPA,
    university_id: Optional[str] = None,
)
    ↓
1. Validación: ¿Supabase configurado?
    ↓
2. Construir doc_data (mapeo de AnalisisAPA a columnas de `documents`)
    - filename: str
    - puntaje_apa: int (0-100)
    - total_errores: int
    - errores_criticos: int
    - errores_menores: int
    - errores_formato: int | None
    - errores_estilo: int | None
    - university_id: UUID (opcional)
    ↓
3. INSERT en `documents` → obtiene document_id
    ↓
4. Construir errores_rows (mapeo de AnalisisAPA.errores a `apa_errors`)
    Para cada error en analisis.errores:
    - document_id: UUID
    - tipo: 'coherencia' | 'formato_apa' | 'estilo'
    - severidad: 'alta' | 'media' | 'baja'
    - regla_apa: str
    - fragmento: str
    - sugerencia: str
    ↓
5. INSERT en `apa_errors` (batch)
    ↓
6. Retorna document_id
```

---

## Tablas Supabase (Schema)

### `documents` (una fila = una revisión)

```sql
id (UUID, PK)
university_id (UUID, FK, nullable)
filename (text)
puntaje_apa (int, 0-100)
total_errores (int)
errores_criticos (int)
errores_menores (int)
errores_formato (int, nullable)
errores_estilo (int, nullable)
created_at (timestamp, auto)
updated_at (timestamp, auto)
```

### `apa_errors` (una fila = un error detectado)

```sql
id (UUID, PK)
document_id (UUID, FK → documents.id)
tipo (text: 'coherencia' | 'formato_apa' | 'estilo')
severidad (enum: 'alta' | 'media' | 'baja')
regla_apa (text)
fragmento (text)
sugerencia (text)
created_at (timestamp, auto)
```

---

## Dependencias

| Módulo | Función |
|--------|---------|
| `schemas.py` | Define `AnalisisAPA`, `ErrorAPA`, `AnalisisEstilo`, `ErrorEstilo` |
| `apa_validator.py` | Retorna `AnalisisAPA` |
| `academic_style.py` | Retorna `AnalisisEstilo` |
| `supabase-py` | Cliente `create_client()` |

**NO edites estas dependencias desde aquí.**

---

## 3 Cambios Comunes (Con Patrones)

### Cambio 1: Añadir Nuevo Campo a `documents`

**Por qué**: `AnalisisAPA` añadió un nuevo campo (ej: `errores_ortografia`).

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/analytics.py
LECTURA PREVIA: Leído CLAUDE-analytics.md

CAMBIO: Mapear nuevo campo en documents

CONTEXTO ACTUAL:
[Copia la sección donde construyes doc_data, líneas ~30-45]

PROBLEMA:
AnalisisAPA ahora tiene un campo nuevo: `errores_ortografia: int | None`.

MEJORA PEDIDA:
1. Añade mapeo en doc_data:
   if analisis.errores_ortografia is not None:
       doc_data["errores_ortografia"] = analisis.errores_ortografia

2. ANTES: Asegúrate que Supabase tiene la columna `errores_ortografia` en `documents`.

SALIDA:
La función guardar_metrica_revision() completa, con el nuevo mapeo.
```

**Lo que esperas recibir**: Función `guardar_metrica_revision()` completa.

---

### Cambio 2: Mejorar Manejo de Errores (Rollback en Transacción)

**Por qué**: Si falla INSERT en `apa_errors` después de insertar `documents`, queda documento huérfano.

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/analytics.py
LECTURA PREVIA: Leído CLAUDE-analytics.md

CAMBIO: Implementar transacción o rollback

PROBLEMA:
Flujo actual:
  1. INSERT documents → obtiene document_id ✅
  2. INSERT apa_errors → FALLA ❌
  Resultado: documento en BD sin errores asociados (huérfano).

SOLUCIÓN PEDIDA:
Implementar una de estas:
Opción A (Recomendada): Usar try/except bloque único — si falla INSERT apa_errors,
  DELETE el documento que acabas de insertar.
Opción B: Registrar el error en log y retornar document_id igual (más permisivo).

SALIDA:
La función guardar_metrica_revision() completa, con manejo transaccional mejorado.
```

**Lo que esperas recibir**: Función mejorada con error handling.

---

### Cambio 3: Añadir Nuevo Tipo de Error a `apa_errors`

**Por qué**: `apa_validator.py` o `academic_style.py` añadieron un nuevo tipo (ej: E07).

**Patrón de Prompt**:

```
ARCHIVO: APA_Validator/modules/analytics.py
LECTURA PREVIA: Leído CLAUDE-analytics.md

CAMBIO: Soportar nuevo tipo de error

CONTEXTO ACTUAL:
[Copia la sección donde mapeas errores en apa_errors, líneas ~50-70]

PROBLEMA:
Se agregó nueva categoría E07 en academic_style.py.
Ahora ErrorEstilo.id puede ser: 'E01' | 'E02' | ... | 'E07'.

MEJORA PEDIDA:
La función guardar_metrica_revision() ya mapea `e.tipo` genéricamente 
(que puede ser 'coherencia', 'formato_apa', o 'estilo').

VERIFICACIÓN:
¿El código actual maneja `e.tipo = 'estilo'` correctamente?
Sí → NO CAMBIOS necesarios.
No → Añade un condicional explícito para tipo='estilo'.

SALIDA:
La función guardar_metrica_revision() completa (sin cambios o mejorada).
```

**Lo que esperas recibir**: Función, confirmando que soporta el nuevo tipo.

---

## Schema de Entrada (Consumidor)

```python
# De apa_validator.py
class AnalisisAPA(BaseModel):
    feedback_texto: str
    errores: list[ErrorAPA]
    puntaje_apa: int
    resumen: ResumenAnalisis
    errores_formato: int | None
    errores_estilo: int | None

# De academic_style.py
class AnalisisEstilo(BaseModel):
    errores: list[ErrorEstilo]
    observacion: str
```

**NO CAMBIAR** — analytics.py consume estos.

---

## Limitaciones (Respetadas)

- ✋ No cambiar nombres de tabla (`documents`, `apa_errors`)
- ✋ No cambiar nombres de columnas sin coordinar con Supabase migrations
- ✋ Siempre usar **service_role key** para inserts backend (bypass RLS)
- ✋ university_id es OPCIONAL (desarrollo local sin institución)
- ✋ No ejecutar deletes masivos sin confirmación
- ✋ Logging en lugar de silent failures

---

## Checklist Antes de Pedir Cambios

- [ ] ¿He identificado si es cambio a mapeo de campos, error handling, o nuevo tipo?
- [ ] ¿He leído la función guardar_metrica_revision() (líneas ~25-80)?
- [ ] ¿Las nuevas columnas existen en Supabase?
- [ ] ¿Sigo usando service_role key?
- [ ] ¿Estoy loguando errores en lugar de silenciarlos?
- [ ] ¿He coordinado con apa_validator.py o academic_style.py si necesario?

---

## Flujo de Edición Recomendado

```
1. Leo CLAUDE-analytics.md (este archivo)
2. Identifico el tipo de cambio (mapeo / error handling / nuevo tipo)
3. Copio el patrón de prompt correspondiente
4. Pego en Claude Extension + personalizo
5. Claude genera el código
6. Copios output → reemplazo en analytics.py
7. pytest tests/test_analytics.py --verbose
8. Si pasa: git commit -m "feat(analytics): [cambio específico]"
```

**CRÍTICO**: Una sesión = UN cambio. No mezcles cambios.

---

## Guía Rápida: Mapeo de Campos

Si necesitas mapear un nuevo campo rápidamente:

```python
# PATRÓN: 
if analisis.<nuevo_campo> is not None:
    doc_data["<nuevo_campo>"] = analisis.<nuevo_campo>

# EJEMPLO: 
if analisis.errores_ortografia is not None:
    doc_data["errores_ortografia"] = analisis.errores_ortografia
```

**Ubicación en código**: Función `guardar_metrica_revision()`, después de mapear `errores_estilo`.

---

## Ejemplos de Cambios Efectivos (Documentados)

*[Se actualiza conforme uses el módulo — patrón que funcionó bien]*

---

*Guía específica para módulo analytics.py*  
*Última actualización: 2026-03-25*
