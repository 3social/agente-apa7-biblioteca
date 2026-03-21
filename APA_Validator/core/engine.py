"""
Core Engine — Fase 9.1
======================
Orquesta el flujo completo de análisis APA 7.

Responsabilidades:
  - Recibe bytes de un .docx y retorna un AnalisisAPA completo.
  - Sin dependencias de Streamlit ni de ninguna capa de UI.
  - Compatible con FastAPI, Streamlit, CLI, tests — cualquier caller.

Flujo:
  1. Extraer secciones del documento (citation_extractor)
  2. Consultar manual APA 7 por sección (knowledge_base + RAG)
  3. Validar formato físico sin LLM (document_formatter) [opcional]
  4. Analizar citas y referencias con LLM (apa_validator)
  5. Analizar estilo académico con LLM (academic_style)    [opcional]
  6. Guardar analítica en Supabase (analytics)             [opcional]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from config.features import FeatureFlags, features as _default_features
from config.settings import settings as _default_settings
from modules.apa_validator import analizar_trabajo
from modules.citation_extractor import extraer_secciones
from modules.document_formatter import validar_formato
from modules.academic_style import analizar_estilo
from modules.analytics import guardar_metrica_revision
from modules.schemas import AnalisisAPA
from rag.knowledge_base import buscar_contexto_completo, inicializar_conocimiento

logger = logging.getLogger(__name__)


# ── Configuración del engine ──────────────────────────────────────────────────

@dataclass
class EngineConfig:
    """
    Parámetros de ejecución del engine.

    Permite sobreescribir settings y flags por llamada — útil para
    multi-tenant (Fase 10) donde cada universidad tiene sus propios flags.
    """
    openai_api_key:       str          = field(default_factory=lambda: _default_settings.OPENAI_API_KEY or "")
    supabase_url:         str | None   = field(default_factory=lambda: _default_settings.SUPABASE_URL)
    supabase_service_key: str | None   = field(default_factory=lambda: _default_settings.SUPABASE_SERVICE_KEY)
    university_id:        str | None   = field(default_factory=lambda: _default_settings.UNIVERSITY_ID)
    manual_pdf_path: str          = field(default_factory=lambda: _default_settings.MANUAL_PDF_PATH)
    features:        FeatureFlags = field(default_factory=lambda: _default_features)


# ── Punto de entrada público ──────────────────────────────────────────────────

def analizar_documento(
    docx_bytes:     bytes,
    nombre_archivo: str = "documento.docx",
    config:         EngineConfig | None = None,
    guardar_analitica: bool = True,
) -> AnalisisAPA:
    """
    Analiza un documento .docx completo y retorna un AnalisisAPA tipado.

    Args:
        docx_bytes:       Contenido binario del archivo .docx.
        nombre_archivo:   Nombre original del archivo (para analítica).
        config:           Configuración del engine. Si es None, usa defaults.
        guardar_analitica: Si True, persiste métricas en Supabase.

    Returns:
        AnalisisAPA con todos los campos completados según los flags activos.

    Raises:
        ValueError: API key faltante, documento vacío o demasiado largo.
        Exception:  Error de red o de la API de OpenAI.
    """
    cfg = config or EngineConfig()

    if not cfg.openai_api_key:
        raise ValueError("OPENAI_API_KEY no configurada.")

    # 1. Extraer secciones
    documento = extraer_secciones(
        docx_bytes,
        completo=cfg.features.extractor_completo,
    )

    # 2. RAG — consultar manual APA 7
    vector_db = inicializar_conocimiento(cfg.manual_pdf_path, cfg.openai_api_key)
    contexto  = buscar_contexto_completo(vector_db, documento, cfg.features)

    # 3. Formato físico (sin LLM) — Fase 0.3
    errores_fmt = None
    if cfg.features.validacion_formato:
        errores_fmt = [e.to_dict() for e in validar_formato(docx_bytes)]

    # 4. Análisis principal con LLM
    analisis = analizar_trabajo(documento, contexto, cfg.openai_api_key)

    # Adjuntar resultados de formato
    if errores_fmt is not None:
        analisis.errores_formato = errores_fmt

    # 5. Estilo académico APA 7 (opcional) — Fase 0.4
    if cfg.features.estilo_academico:
        try:
            resultado_estilo = analizar_estilo(documento, cfg.openai_api_key)
            analisis.errores_estilo = [e.to_dict() for e in resultado_estilo.errores]
            analisis.coherencia = {
                "observacion_estilo": resultado_estilo.observacion_general
            }
        except ValueError as e:
            logger.info("Análisis de estilo omitido: %s", e)

    # 6. Analítica en Supabase
    if guardar_analitica:
        guardar_metrica_revision(
            cfg.supabase_url,
            cfg.supabase_service_key,   # service_role bypasea RLS
            nombre_archivo,
            analisis,
            university_id=cfg.university_id,
        )

    return analisis
