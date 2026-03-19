"""
Conector de analítica institucional con Supabase.

Lee directamente del objeto AnalisisAPA tipado — sin keyword matching.
El esquema de Supabase se migrará al modelo relacional completo en Fase 10.
"""

from supabase import Client, create_client
import streamlit as st
from .schemas import AnalisisAPA


def guardar_metrica_revision(
    supabase_url: str,
    supabase_key: str,
    nombre_archivo: str,
    analisis: AnalisisAPA,
) -> bool:
    """
    Persiste las métricas de una revisión en Supabase.

    Usa datos estructurados del objeto AnalisisAPA — no texto libre.
    Esto garantiza que los datos sean correctos independientemente
    de cómo el LLM redacte su respuesta.
    """
    if not supabase_url or not supabase_key:
        st.sidebar.warning("⚠️ Supabase no configurado — analítica desactivada.")
        return False

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        tipos = [e.tipo for e in analisis.errores]
        error_mas_comun = max(set(tipos), key=tipos.count) if tipos else "ninguno"

        data = {
            # Identificación del documento
            "alumno": nombre_archivo,

            # Métricas de calidad APA (vienen del JSON estructurado)
            "puntaje_apa":       analisis.puntaje_apa,
            "total_errores":     analisis.resumen.total_errores,
            "errores_criticos":  analisis.resumen.errores_criticos,
            "errores_menores":   analisis.resumen.errores_menores,

            # Desglose de tipos de error para analítica de tendencias
            "citas_huerfanas":   sum(1 for t in tipos if t == "cita_huerfana"),
            "refs_sobrantes":    sum(1 for t in tipos if t == "referencia_sobrante"),
            "error_mas_comun":   error_mas_comun,
        }

        supabase.table("revisiones_apa").insert(data).execute()
        return True

    except Exception as e:
        st.sidebar.warning(f"⚠️ Error al guardar analítica: {e}")
        return False
