"""
Fase 0.4 — Análisis de Estilo Académico APA 7
=============================================
Detecta problemas de estilo que Grammarly no cubre:

  E01 — Lenguaje con sesgo (APA 7, Capítulo 5): terminología de identidad,
        etiquetas reduccionistas, lenguaje sobre género, raza, discapacidad.
  E02 — Registro informal: coloquialismos, jerga, tono no académico.
  E03 — Primera persona: uso incorrecto según el contexto del trabajo.
  E04 — Afirmaciones sin respaldo: generalizaciones sin cita de respaldo.
  E05 — Verbosidad y redundancia académica.
  E06 — Voz pasiva excesiva (APA 7 prefiere voz activa).

Usa LLM con Structured Outputs — garantiza schema válido.
Módulo opcional: se activa con FEATURE_ESTILO_ACADEMICO=true.
"""

from openai import OpenAI, LengthFinishReasonError

from .schemas import DocumentoAPA, AnalisisEstilo


# Límites de caracteres — este módulo analiza solo el cuerpo redactado.
_MAX_CUERPO  = 5_000
_MAX_SECCION = 400

_PROMPT_SISTEMA = """\
Eres un experto en escritura académica universitaria latinoamericana y en el \
Manual APA 7ma edición. Tu tarea es analizar el ESTILO ACADÉMICO del trabajo, \
no la gramática mecánica (ortografía, puntuación) — para eso existen otras herramientas.

Detecta exclusivamente los siguientes problemas de estilo académico APA 7:

1. LENGUAJE CON SESGO (APA 7, Capítulo 5)
   - Terminología que estigmatiza por identidad: género, raza, edad, discapacidad,
     orientación sexual, origen étnico, estatus socioeconómico.
   - Ejemplos incorrectos: "los discapacitados", "las mujeres son más emocionales",
     "el hombre primitivo". Usar en cambio: "personas con discapacidad", etc.

2. REGISTRO INFORMAL
   - Coloquialismos, jerga, expresiones de habla cotidiana que no corresponden
     a un texto académico.
   - Ejemplos: "la cosa es que", "o sea", "un montón de", "súper importante".

3. PRIMERA PERSONA
   - APA 7 PERMITE "yo" y "nosotros" cuando el autor describe sus propias acciones
     ("analicé los datos", "encontramos que...").
   - Problema real: uso de primera persona para hacer afirmaciones no sustentadas
     ("yo creo que", "en mi opinión", "me parece que") sin respaldo empírico.
   - También detecta el uso innecesario de tercera persona impersonal como
     evasión formal ("el investigador procedió a...").

4. AFIRMACIONES SIN RESPALDO
   - Afirmaciones presentadas como hechos sin cita: "está comprobado que",
     "es evidente que", "todos saben que", "la ciencia ha demostrado que",
     "es bien sabido que", "actualmente se sabe que".

5. VERBOSIDAD Y REDUNDANCIA
   - Frases que repiten innecesariamente: "anteriormente antes mencionado",
     "en el presente trabajo de investigación", "a través del uso de la utilización de",
     "en base a los resultados obtenidos se puede concluir que".

6. VOZ PASIVA EXCESIVA
   - APA 7 prefiere voz activa para mayor claridad.
   - Flagear párrafos con densidad alta de voz pasiva cuando hay alternativa activa clara.
   - No flagear voz pasiva cuando es la forma natural o cuando el sujeto es desconocido.

IMPORTANTE:
- Analiza ÚNICAMENTE el texto que se te proporcione. Si es un adelanto, evalúa solo lo presente.
- No penalices lo que no está — puede ser un documento parcial.
- Máximo 10 errores. Si hay más, reporta los más importantes por severidad.
- Tono pedagógico: explica por qué es un problema y cómo mejorar.
- Si el texto no tiene problemas de estilo, retorna lista vacía con observación positiva.
"""


def _construir_texto(documento: DocumentoAPA) -> str:
    """Extrae las partes redactadas del documento para análisis de estilo."""
    partes = []

    if documento.abstract:
        partes.append(f"RESUMEN/ABSTRACT:\n{documento.abstract[:_MAX_SECCION]}")

    if documento.cuerpo:
        partes.append(f"CUERPO:\n{documento.cuerpo[:_MAX_CUERPO]}")

    if documento.apendices:
        partes.append(f"APÉNDICES:\n{documento.apendices[:_MAX_SECCION]}")

    return "\n\n".join(partes) if partes else ""


def analizar_estilo(
    documento: DocumentoAPA,
    api_key: str,
) -> AnalisisEstilo:
    """
    Analiza el estilo académico APA 7 del documento y retorna un AnalisisEstilo tipado.

    Args:
        documento: Secciones extraídas del .docx por citation_extractor.
        api_key:   OpenAI API key.

    Returns:
        AnalisisEstilo con lista de errores y observación general.

    Raises:
        ValueError: Documento vacío, demasiado largo o respuesta rechazada.
        Exception:  Error de red o de la API de OpenAI.
    """
    texto = _construir_texto(documento)

    if not texto.strip():
        raise ValueError(
            "El documento no tiene texto de cuerpo para analizar el estilo académico."
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _PROMPT_SISTEMA},
                {"role": "user",   "content": f"--- TEXTO DEL TRABAJO ---\n{texto}"},
            ],
            response_format=AnalisisEstilo,
            temperature=0.2,
        )
    except LengthFinishReasonError as e:
        raise ValueError(
            "El texto es demasiado largo para analizar el estilo completo. "
            "Considera dividirlo por secciones."
        ) from e

    resultado = response.choices[0].message

    if resultado.refusal:
        raise ValueError(f"El modelo rechazó el análisis de estilo: {resultado.refusal}")

    return resultado.parsed
