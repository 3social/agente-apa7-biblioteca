"""
Conector de analítica institucional con Supabase.

Escribe en el esquema multitenant (Fase 10):
  documents  — una fila por documento analizado
  apa_errors — una fila por error de cita/referencia detectado

Lee directamente del objeto AnalisisAPA tipado — sin keyword matching.
"""

import logging
from typing import Optional

from supabase import Client, create_client

from .schemas import AnalisisAPA

logger = logging.getLogger(__name__)


def guardar_metrica_revision(
    supabase_url:    str | None,
    supabase_key:    str | None,
    nombre_archivo:  str,
    analisis:        AnalisisAPA,
    university_id:   Optional[str] = None,
) -> Optional[str]:
    """
    Persiste las métricas de una revisión en Supabase.

    Args:
        supabase_url:   URL del proyecto Supabase.
        supabase_key:   Service role key (bypasea RLS).
        nombre_archivo: Nombre original del .docx.
        analisis:       Resultado tipado del análisis.
        university_id:  UUID de la universidad. Si es None, la fila queda sin tenant
                        (válido en desarrollo local sin universidad configurada).

    Returns:
        UUID del documento insertado, o None si hubo error o Supabase no está configurado.
    """
    if not supabase_url or not supabase_key:
        logger.warning("Supabase no configurado — analítica desactivada.")
        return None

    try:
        # Usa service_role key para bypasear RLS en inserts del backend.
        supabase: Client = create_client(supabase_url, supabase_key)

        # 1. Insertar documento y obtener su ID
        doc_data = {
            "filename":         nombre_archivo,
            "puntaje_apa":      analisis.puntaje_apa,
            "total_errores":    analisis.resumen.total_errores,
            "errores_criticos": analisis.resumen.errores_criticos,
            "errores_menores":  analisis.resumen.errores_menores,
        }

        if university_id:
            doc_data["university_id"] = university_id

        if analisis.errores_formato is not None:
            doc_data["errores_formato"] = analisis.errores_formato

        if analisis.errores_estilo is not None:
            doc_data["errores_estilo"] = analisis.errores_estilo

        response = supabase.table("documents").insert(doc_data).execute()

        if not response.data:
            logger.warning("Supabase no retornó datos al insertar documento.")
            return None

        document_id = response.data[0]["id"]

        # 2. Insertar errores APA normalizados (si hay)
        if analisis.errores:
            errores_rows = [
                {
                    "document_id": document_id,
                    "tipo":        e.tipo,
                    "severidad":   e.severidad.value,
                    "regla_apa":   e.regla_apa,
                    "fragmento":   e.fragmento,
                    "sugerencia":  e.sugerencia,
                }
                for e in analisis.errores
            ]
            supabase.table("apa_errors").insert(errores_rows).execute()

        return document_id

    except Exception as e:
        logger.warning("Error al guardar analítica en Supabase: %s", e)
        return None
