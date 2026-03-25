"""
Schemas de datos del sistema APA Validator.

Define los contratos de entrada/salida entre módulos.
Todos los módulos futuros (grammar_checker, document_formatter,
semantic_analyzer) agregarán sus campos aquí.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


# ── Documento de entrada ──────────────────────────────────────────────────────

class Encabezado(BaseModel):
    """Encabezado detectado en el cuerpo del documento."""
    nivel: int = Field(ge=1, le=5, description="Nivel del encabezado (1=H1 ... 5=H5).")
    texto: str


class DocumentoAPA(BaseModel):
    """
    Representación estructurada de un documento APA 7.
    Resultado del citation_extractor.

    Los campos vacíos indican que la sección no fue encontrada
    o que el feature flag correspondiente está desactivado.
    Esto permite que los módulos de análisis trabajen con lo que
    esté disponible sin romper el flujo.
    """
    portada:     str              = ""
    abstract:    str              = ""
    cuerpo:      str              = ""
    encabezados: List[Encabezado] = Field(default_factory=list)
    referencias: str              = ""
    apendices:   str              = ""
    tablas:      List[str]        = Field(default_factory=list)
    figuras:     List[str]        = Field(default_factory=list)


# ── Resultado del análisis ────────────────────────────────────────────────────


class Severidad(str, Enum):
    alta  = "alta"
    media = "media"
    baja  = "baja"


class ErrorAPA(BaseModel):
    """Un error de citación o referencia APA detectado en el documento."""

    tipo: str = Field(
        description=(
            "Categoría del error. Valores esperados: "
            "cita_huerfana, referencia_sobrante, formato_autor, "
            "formato_año, formato_titulo, formato_editorial, "
            "formato_doi, cita_texto_incompleta, orden_referencias, otro."
        )
    )
    severidad: Severidad = Field(
        description="Impacto del error: alta (rompe norma), media (defecto parcial), baja (estilo)."
    )
    fragmento: str = Field(
        description="Fragmento exacto del texto del alumno donde ocurre el error."
    )
    regla_apa: str = Field(
        description="Sección del Manual APA 7 que se viola. Ejemplo: 'Sección 8.11'."
    )
    sugerencia: str = Field(
        description="Corrección propuesta, redactada de forma pedagógica y clara."
    )


class ResumenAnalisis(BaseModel):
    """Conteo agregado de errores para analítica institucional."""

    total_errores:    int = Field(ge=0)
    errores_criticos: int = Field(ge=0, description="Errores de severidad alta.")
    errores_menores:  int = Field(ge=0, description="Errores de severidad media o baja.")

    @field_validator("errores_criticos", "errores_menores")
    @classmethod
    def no_supera_total(cls, v, info):
        # Validación cruzada: la suma de partes no debe superar el total.
        # Pydantic ejecuta los validators en orden de declaración,
        # por lo que 'total_errores' ya existe en info.data cuando llega aquí.
        if "total_errores" in info.data and v > info.data["total_errores"]:
            raise ValueError("Los subtotales no pueden superar total_errores.")
        return v


class TipoErrorEstilo(str, Enum):
    sesgo_lenguaje        = "sesgo_lenguaje"
    registro_informal     = "registro_informal"
    primera_persona       = "primera_persona"
    afirmacion_sin_respaldo = "afirmacion_sin_respaldo"
    verbosidad            = "verbosidad"
    voz_pasiva_excesiva   = "voz_pasiva_excesiva"
    otro                  = "otro"


class ErrorEstilo(BaseModel):
    """Un problema de estilo académico APA 7 detectado por el LLM."""
    tipo: TipoErrorEstilo = Field(
        description=(
            "Categoría del problema: sesgo_lenguaje, registro_informal, "
            "primera_persona, afirmacion_sin_respaldo, verbosidad, "
            "voz_pasiva_excesiva, otro."
        )
    )
    severidad: Severidad = Field(
        description="alta = viola norma APA 7 explícita; media = debilita el trabajo; baja = recomendación."
    )
    fragmento: str = Field(
        description="Fragmento exacto del texto del alumno donde ocurre el problema."
    )
    capitulo_apa: str = Field(
        description="Referencia al capítulo o sección APA 7. Ejemplo: 'APA 7, Capítulo 5.2'."
    )
    sugerencia: str = Field(
        description="Cómo reescribir o corregir el fragmento. Tono pedagógico."
    )

    def to_dict(self) -> dict:
        return {
            "tipo":        self.tipo.value,
            "severidad":   self.severidad.value,
            "fragmento":   self.fragmento,
            "capitulo_apa": self.capitulo_apa,
            "sugerencia":  self.sugerencia,
        }


class AnalisisEstilo(BaseModel):
    """Resultado completo del análisis de estilo académico APA 7."""
    errores: List[ErrorEstilo] = Field(
        description="Lista de problemas de estilo encontrados. Vacía si el texto cumple."
    )
    observacion_general: str = Field(
        description=(
            "Párrafo breve (2-3 oraciones) con la valoración general del estilo académico. "
            "Tono constructivo, menciona fortalezas y áreas de mejora."
        )
    )


class AnalisisAPA(BaseModel):
    """
    Resultado completo del análisis APA.

    Este es el contrato central del sistema. Cualquier módulo futuro
    (grammar_checker, document_formatter, semantic_analyzer) extenderá
    este schema agregando campos opcionales con default=None para
    mantener retrocompatibilidad.
    """

    feedback_texto: str = Field(
        description=(
            "Reporte completo en formato Markdown para mostrar al alumno. "
            "Debe tener secciones: ## Coherencia, ## Formato APA 7, ## Correcciones. "
            "Tono pedagógico, claro y constructivo."
        )
    )
    errores: List[ErrorAPA] = Field(
        description="Lista detallada de cada error APA encontrado."
    )
    puntaje_apa: int = Field(
        ge=0,
        le=100,
        description=(
            "Puntaje global de cumplimiento APA 7. "
            "0 = no cumple ninguna norma. 100 = cumplimiento perfecto."
        )
    )
    resumen: ResumenAnalisis

    # --- Campos de módulos opcionales (rellenados por código, no por el LLM) ---
    errores_formato:   Optional[List[dict]] = Field(default=None, description="document_formatter.py — Fase 0.3")
    errores_estilo:    Optional[List[dict]] = Field(default=None, description="academic_style.py — Fase 0.4 (opcional)")
    coherencia:        Optional[dict]       = Field(default=None, description="Reservado")


class LLMAnalisisAPA(BaseModel):
    """
    Schema reducido para la llamada a OpenAI Structured Outputs.
    Solo incluye los campos que el LLM debe rellenar — sin dict ni Optional[dict]
    que rompen la validación de additionalProperties de OpenAI.
    Los campos opcionales (errores_formato, errores_estilo) los agrega el código
    después de recibir la respuesta del LLM.
    """
    feedback_texto: str = Field(
        description=(
            "Reporte completo en formato Markdown para mostrar al alumno. "
            "Secciones: ## Coherencia, ## Formato APA 7, ## Correcciones. "
            "Tono pedagógico, claro y constructivo."
        )
    )
    errores:    List[ErrorAPA]     = Field(description="Lista detallada de cada error APA encontrado.")
    puntaje_apa: int               = Field(ge=0, le=100, description="Puntaje global APA 7 (0-100).")
    resumen:    ResumenAnalisis
