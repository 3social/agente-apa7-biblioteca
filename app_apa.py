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

# 1. CONFIGURACIÓN SEGURA
load_dotenv()
API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

# Inicializar Supabase solo si las claves existen
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("❌ Error: Faltan las credenciales de Supabase en los Secrets.")
    st.stop()

# --- FUNCIONES DE APOYO (DEFINIDAS ANTES DEL FLUJO) ---

def extraer_secciones(file_bytes):
    """Extrae y separa el cuerpo del texto de las referencias."""
    doc = docx.Document(io.BytesIO(file_bytes))
    cuerpo, refs = [], []
    en_refs = False
    marcas = ["referencias", "bibliografía", "lista de referencias", "obras citadas"]
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t: continue
        if t.lower().replace(":", "") in marcas:
            en_refs = True
            continue
        if en_refs: refs.append(t)
        else: cuerpo.append(t)
    return "\n".join(cuerpo), "\n".join(refs)

@st.cache_resource
def inicializar_conocimiento(ruta_pdf):
    """Carga el PDF y crea el índice RAG."""
    if not os.path.exists(ruta_pdf):
        return None
    loader = PyPDFLoader(ruta_pdf)
    docs = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(loader.load())
    return FAISS.from_documents(docs, OpenAIEmbeddings(openai_api_key=API_KEY))

def analizar_con_rag(cuerpo, refs, vector_store):
    """Analiza el trabajo usando el manual PDF como referencia."""
    consulta = f"Reglas APA 7 para: {cuerpo[:300]}... {refs[:300]}"
    docs_relevantes = vector_store.similarity_search(consulta, k=3) if vector_store else []
    contexto = "\n\n".join([d.page_content for d in docs_relevantes])
    
    client = OpenAI(api_key=API_KEY)
    prompt = (
        "Eres un bibliotecario experto en APA 7. Genera un REPORTE DE FEEDBACK.\n"
        "Usa el manual oficial proporcionado para justificar tus correcciones.\n"
        "1. COHERENCIA: Citas vs Referencias.\n"
        "2. FORMATO: Basado en el manual.\n"
        "3. CORRECCIONES: Sé pedagógico."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": f"MANUAL:\n{contexto}\n\nTRABAJO:\n{cuerpo}\n\nREFS:\n{refs}"}]
    )
    return response.choices[0].message.content

def guardar_en_supa(nombre, feedback):
    """Guarda métricas en Supabase."""
    try:
        data = {
            "alumno": nombre,
            "citas_huerfanas": 1 if "huérfana" in feedback.lower() else 0,
            "refs_sobrantes": 1 if "sobrante" in feedback.lower() else 0,
            "error_mas_comun": "Formato" if "sangría" in feedback.lower() else "Coherencia"
        }
        supabase.table("revisiones_apa").insert(data).execute()
        st.sidebar.success("📊 Analítica guardada.")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error analítica: {e}")

# --- INTERFAZ STREAMLIT ---
st.title("📚 Agente APA 7 - Biblioteca Profesional")
st.sidebar.header("Estado")

vector_db = inicializar_conocimiento("manual_apa7.pdf")
if vector_db: st.sidebar.success("✅ Manual APA 7 Activo")

archivo = st.file_uploader("Sube el archivo .docx del alumno", type=["docx"])

if archivo:
    if st.button("🚀 Iniciar Análisis"):
        with st.spinner("Procesando..."):
            # 1. Extraer (Función ahora definida correctamente)
            cuerpo, refs = extraer_secciones(archivo.read())
            
            # 2. Analizar
            resultado = analizar_con_rag(cuerpo, refs, vector_db)
            
            # 3. Guardar en Supabase
            guardar_en_supa(archivo.name, resultado)
            
            # 4. Mostrar y Descargar
            st.success("¡Análisis completado!")
            st.markdown(resultado)
            
            doc_out = docx.Document()
            doc_out.add_heading(f"Reporte APA - {archivo.name}", 0)
            for line in resultado.split('\n'): doc_out.add_paragraph(line)
            buffer = io.BytesIO()
            doc_out.save(buffer)
            st.download_button("📥 Descargar Reporte Word", buffer.getvalue(), 
                               file_name=f"Feedback_APA_{archivo.name}", 
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
