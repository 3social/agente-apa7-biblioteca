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
import docx
import io
import os
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client, Client

# Librerías RAG
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 1. CARGA DE CONFIGURACIÓN SEGURA
load_dotenv()
API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MOTOR DE CONOCIMIENTO (RAG) ---
@st.cache_resource
def inicializar_conocimiento(ruta_pdf):
    loader = PyPDFLoader(ruta_pdf)
    docs = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(loader.load())
    return FAISS.from_documents(docs, OpenAIEmbeddings(openai_api_key=API_KEY))

# --- FUNCIÓN DE MEMORIA INSTITUCIONAL (SUPABASE) ---
def guardar_en_memoria_institucional(nombre_archivo, feedback_texto):
    """Extrae datos del feedback y los guarda en Supabase para analítica."""
    try:
        # Lógica simple para extraer métricas del texto de la IA (puedes mejorarla con regex)
        citas_huerfanas = 1 if "Cita huérfana" in feedback_texto else 0
        refs_sobrantes = 1 if "Referencia sobrante" in feedback_texto else 0
        
        data = {
            "alumno": nombre_archivo,
            "citas_huerfanas": citas_huerfanas,
            "refs_sobrantes": refs_sobrantes,
            "error_mas_comun": "Formato APA" if "sangría" in feedback_texto.lower() else "Coherencia",
            "feedback_ia": feedback_texto[:500] # Guardamos solo un resumen
        }
        supabase.table("revisiones_apa").insert(data).execute()
        st.sidebar.info("📊 Datos guardados en la memoria institucional.")
    except Exception as e:
        st.sidebar.error(f"⚠️ Error al guardar en Supabase: {e}")

# --- INTERFAZ Y LÓGICA ---
st.title("📚 Agente APA 7 con Memoria Institucional")

# (Aquí va el resto de tus funciones: extraer_secciones, analizar_con_rag...)

# --- DENTRO DEL BOTÓN DE ANÁLISIS ---
if st.button("🚀 Iniciar Análisis Profesional"):
    with st.spinner("Analizando y guardando en base de datos..."):
        cuerpo, refs = extraer_secciones(archivo.read())
        vector_db = inicializar_conocimiento("manual_apa7.pdf")
        resultado = analizar_con_rag(cuerpo, refs, vector_db)
        
        # GUARDAR EN SUPABASE (FEEDBACK LOOP)
        guardar_en_memoria_institucional(archivo.name, resultado)
        
        st.success("¡Análisis Finalizado!")
        st.markdown(resultado)
        # (Botón de descarga...)
