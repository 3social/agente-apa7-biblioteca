"""
Motor de análisis APA 7.

Recibe un DocumentoAPA (con las secciones extraídas) y un dict de contextos
del manual por sección. Retorna un AnalisisAPA tipado con Structured Outputs
de OpenAI — garantiza schema válido en el 100% de los casos.
"""

from openai import OpenAI, LengthFinishReasonError
from .schemas import DocumentoAPA, AnalisisAPA


# Límites de caracteres por sección para controlar el consumo de tokens.
# En Fase 9, esto se reemplaza con chunking y procesamiento asíncrono.
_MAX_CUERPO   = 6_000
_MAX_REFS     = 2_000
_MAX_SECCION  = 500    # portada, abstract, apéndices
_MAX_CONTEXTO = 500    # por sección del manual

_PROMPT_SISTEMA = """\
Eres un bibliotecario experto en APA 7ma edición. Analiza el trabajo académico del alumno.

Analiza ÚNICAMENTE las secciones que se te proporcionen en el trabajo.
Si una sección no aparece (portada, abstract, apéndices, etc.),
no la menciones ni la penalices — simplemente no está en este documento.

Tu análisis debe cubrir:
1. COHERENCIA: citas huérfanas (citadas en texto sin referencia) y referencias
   sobrantes (en lista sin citar en el texto).
2. FORMATO APA 7: verifica cada elemento presente contra las reglas del manual
   proporcionadas. Solo penaliza lo que el manual específicamente indica.
3. CORRECCIONES: por cada error, el fragmento exacto, la regla violada
   y una corrección pedagógica con el ejemplo de la forma correcta.

Reglas para feedback_texto:
- Markdown con secciones ## Coherencia, ## Formato APA 7, ## Correcciones.
- Tono constructivo y pedagógico, nunca punitivo.
- Si una sección no tiene errores, indícalo positivamente.

Reglas para puntaje_apa (0-100):
- 90-100: solo errores menores de estilo.
- 70-89: errores de formato que no afectan coherencia.
- 50-69: errores moderados de coherencia o formato.
- 0-49: errores críticos que comprometen la integridad académica.

Reglas para severidad de errores:
- alta:  viola explícitamente una norma APA (cita sin referencia, autor faltante).
- media: defecto parcial de formato (coma faltante, año incorrecto).
- baja:  recomendación de estilo, no norma obligatoria.
"""


def _construir_contexto(contexto: dict[str, str]) -> str:
    """Formatea el dict de contextos por sección para el prompt."""
    if not contexto:
        return "(No se encontró manual APA 7 disponible.)"
    partes = []
    for seccion, texto in contexto.items():
        if texto.strip():
            partes.append(f"=== REGLAS APA 7: {seccion.upper()} ===\n{texto[:_MAX_CONTEXTO]}")
    return "\n\n".join(partes) if partes else "(Sin contexto disponible.)"


def _construir_documento(documento: DocumentoAPA) -> str:
    """Formatea el DocumentoAPA para el prompt, incluyendo solo secciones con contenido."""
    partes = []

    if documento.portada:
        partes.append(f"PORTADA:\n{documento.portada[:_MAX_SECCION]}")

    if documento.abstract:
        partes.append(f"RESUMEN / ABSTRACT:\n{documento.abstract[:_MAX_SECCION]}")

    if documento.encabezados:
        estructura = "\n".join(
            f"{'  ' * (e.nivel - 1)}H{e.nivel}: {e.texto}"
            for e in documento.encabezados
        )
        partes.append(f"ESTRUCTURA DE ENCABEZADOS:\n{estructura}")

    if documento.cuerpo:
        partes.append(f"CUERPO DEL TEXTO:\n{documento.cuerpo[:_MAX_CUERPO]}")

    if documento.referencias:
        partes.append(f"LISTA DE REFERENCIAS:\n{documento.referencias[:_MAX_REFS]}")

    if documento.tablas:
        partes.append("TÍTULOS DE TABLAS:\n" + "\n".join(documento.tablas))

    if documento.figuras:
        partes.append("TÍTULOS DE FIGURAS:\n" + "\n".join(documento.figuras))

    if documento.apendices:
        partes.append(f"APÉNDICES:\n{documento.apendices[:_MAX_SECCION]}")

    return "\n\n".join(partes) if partes else "(Documento vacío o sin secciones detectadas.)"


def analizar_trabajo(
    documento: DocumentoAPA,
    contexto: dict[str, str],
    api_key: str,
) -> AnalisisAPA:
    """
    Analiza el trabajo del alumno y retorna un AnalisisAPA tipado.

    Args:
        documento: Secciones extraídas del .docx por citation_extractor.
        contexto:  Reglas del Manual APA 7 por sección, desde knowledge_base.
        api_key:   OpenAI API key.

    Returns:
        AnalisisAPA con feedback, errores tipificados, puntaje y resumen.

    Raises:
        ValueError: Documento demasiado largo o respuesta rechazada por el modelo.
        Exception:  Error de red o de la API de OpenAI.
    """
    client = OpenAI(api_key=api_key)

    prompt_usuario = (
        f"--- REGLAS DEL MANUAL APA 7 ---\n{_construir_contexto(contexto)}\n\n"
        f"--- TRABAJO DEL ALUMNO ---\n{_construir_documento(documento)}"
    )

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _PROMPT_SISTEMA},
                {"role": "user",   "content": prompt_usuario},
            ],
            response_format=AnalisisAPA,
            temperature=0.2,
        )
    except LengthFinishReasonError as e:
        raise ValueError(
            "El documento es demasiado largo para analizarlo completo. "
            "Considera dividirlo por secciones."
        ) from e

    resultado = response.choices[0].message

    if resultado.refusal:
        raise ValueError(f"El modelo rechazó el análisis: {resultado.refusal}")

    return resultado.parsed
