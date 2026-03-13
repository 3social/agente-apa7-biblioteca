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

# ESTO SOLUCIONA EL ERROR DE MÓDULOS:
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. IMPORTACIONES DE TUS MÓDULOS (LA MAGIA MODULAR)
from config.settings import settings
from modules.citation_extractor import extraer_secciones
from modules.apa_validator import analizar_trabajo
from modules.analytics import guardar_metrica_revision
from rag.knowledge_base import inicializar_conocimiento, buscar_en_manual
from reports.report_generator import generar_reporte_docx

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Agente APA 7 - Biblioteca", page_icon="📚", layout="centered")

st.title("📚 Plataforma Profesional APA 7")
st.markdown("### Automatización y Analítica Institucional")

# --- BARRA LATERAL (ESTADO) ---
with st.sidebar:
    st.header("⚙️ Estado del Sistema")
    
    # Verificar API Keys
    if not settings.OPENAI_API_KEY:
        st.error("❌ Falta OpenAI API Key")
        st.stop()
        
    # Inicializar RAG (Manual PDF)
    vector_db = inicializar_conocimiento(settings.MANUAL_PDF_PATH, settings.OPENAI_API_KEY)
    if vector_db:
        st.success("✅ Manual APA 7 Activo")
    else:
        st.warning("⚠️ No se encontró manual_apa7.pdf")

# --- FLUJO PRINCIPAL ---
archivo = st.file_uploader("Sube el trabajo del alumno (.docx)", type=["docx"])

if archivo:
    if st.button("🚀 Iniciar Análisis Profesional"):
        with st.spinner("El Agente está analizando y consultando el manual..."):
            try:
                # 1. Extracción (Módulo: citation_extractor)
                cuerpo, refs = extraer_secciones(archivo.read())
                
                # 2. Búsqueda en Manual (Módulo: knowledge_base)
                contexto = buscar_en_manual(vector_db, f"{cuerpo[:200]} {refs[:200]}")
                
                # 3. Análisis con IA (Módulo: apa_validator)
                feedback = analizar_trabajo(cuerpo, refs, contexto, settings.OPENAI_API_KEY)
                
                # 4. Guardar Analítica (Módulo: analytics)
                guardar_metrica_revision(
                    settings.SUPABASE_URL, 
                    settings.SUPABASE_KEY, 
                    archivo.name, 
                    feedback
                )
                
                # 5. Mostrar Resultados
                st.success("¡Análisis Completado!")
                st.markdown("---")
                st.markdown(feedback)
                
                # 6. Generar y Descargar Reporte (Módulo: report_generator)
                reporte_word = generar_reporte_docx(feedback, archivo.name)
                st.download_button(
                    label="📥 Descargar Reporte para el Alumno",
                    data=reporte_word,
                    file_name=f"Reporte_APA_{archivo.name}",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("Desarrollado para la optimización de servicios bibliotecarios.")
