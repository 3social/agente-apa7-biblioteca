"""
APA Validator AI
Sistema de Validación de Citas y Referencias APA mediante Inteligencia Artificial

Copyright (c) 2026 Michael González
All rights reserved.

Este software es propiedad de Michael González.
Queda prohibida la reproducción, distribución, modificación
o uso del código sin autorización expresa del autor.
"""

import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from config.features import features
from modules.citation_extractor import extraer_secciones
from modules.apa_validator import analizar_trabajo
from modules.analytics import guardar_metrica_revision
from modules.schemas import Severidad
from rag.knowledge_base import inicializar_conocimiento, buscar_contexto_completo
from reports.report_generator import generar_reporte_docx


# ── Configuración de la interfaz ──────────────────────────────────────────────

st.set_page_config(
    page_title="Agente APA 7 - Biblioteca",
    page_icon="📚",
    layout="centered",
)

st.title("📚 Plataforma Profesional APA 7")
st.markdown("### Automatización y Analítica Institucional")


# ── Barra lateral ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Estado del Sistema")

    if not settings.OPENAI_API_KEY:
        st.error("❌ Falta OpenAI API Key")
        st.stop()

    vector_db = inicializar_conocimiento(settings.MANUAL_PDF_PATH, settings.OPENAI_API_KEY)
    if vector_db:
        st.success("✅ Manual APA 7 Activo")
    else:
        st.warning("⚠️ No se encontró manual_apa7.pdf")

    # Módulos activos — muestra al equipo qué está habilitado en este ambiente.
    st.markdown("---")
    st.caption("**Módulos activos**")
    for nombre, icono in features.resumen_sidebar().items():
        st.caption(f"{icono} {nombre.replace('_', ' ').title()}")


# ── Flujo principal ───────────────────────────────────────────────────────────

archivo = st.file_uploader("Sube el trabajo del alumno (.docx)", type=["docx"])

if archivo:
    if st.button("🚀 Iniciar Análisis Profesional"):
        with st.spinner("El Agente está analizando y consultando el manual..."):
            try:
                # 1. Extraer secciones del documento
                #    completo=True activa el extractor de todas las secciones APA 7.
                #    completo=False mantiene el comportamiento original (cuerpo + refs).
                documento = extraer_secciones(
                    archivo.read(),
                    completo=features.extractor_completo,
                )

                # 2. Buscar reglas en el Manual APA 7 por sección
                #    Solo consulta las secciones que el documento tiene Y
                #    cuyo feature flag está activo. Reduce tokens y ruido.
                contexto = buscar_contexto_completo(vector_db, documento, features)

                # 3. Análisis con IA — retorna AnalisisAPA tipado
                analisis = analizar_trabajo(documento, contexto, settings.OPENAI_API_KEY)

                # 4. Guardar analítica en Supabase (datos estructurados, sin keyword matching)
                guardar_metrica_revision(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY,
                    archivo.name,
                    analisis,
                )

                # ── Mostrar resultados ─────────────────────────────────────────

                st.success("¡Análisis Completado!")
                st.markdown("---")

                # Métricas de resumen
                col1, col2, col3 = st.columns(3)
                col1.metric("Puntaje APA",       f"{analisis.puntaje_apa} / 100")
                col2.metric("Errores críticos",   analisis.resumen.errores_criticos)
                col3.metric("Errores menores",    analisis.resumen.errores_menores)

                # Reporte narrativo para el alumno
                st.markdown("---")
                st.markdown(analisis.feedback_texto)

                # Lista de errores estructurados con color por severidad
                if analisis.errores:
                    with st.expander(f"Ver {analisis.resumen.total_errores} errores detallados"):
                        for error in analisis.errores:
                            color = (
                                "🔴" if error.severidad == Severidad.alta  else
                                "🟡" if error.severidad == Severidad.media else
                                "🟢"
                            )
                            st.markdown(
                                f"{color} **{error.tipo.replace('_', ' ').title()}**"
                                f" — _{error.regla_apa}_"
                            )
                            st.caption(f'Fragmento: "{error.fragmento}"')
                            st.info(f"Sugerencia: {error.sugerencia}")

                # Descarga del reporte Word
                reporte_word = generar_reporte_docx(analisis.feedback_texto, archivo.name)
                st.download_button(
                    label="📥 Descargar Reporte para el Alumno",
                    data=reporte_word,
                    file_name=f"Reporte_APA_{archivo.name}",
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    ),
                )

            except ValueError as e:
                st.warning(f"⚠️ {e}")
            except Exception as e:
                st.error(f"Error inesperado: {e}")


# ── Pie de página ─────────────────────────────────────────────────────────────

st.markdown("---")
st.caption("Desarrollado para la optimización de servicios bibliotecarios.")
