import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

@st.cache_resource
def inicializar_conocimiento(ruta_pdf, api_key):
    """Carga el PDF y crea el índice RAG de forma eficiente."""
    if not os.path.exists(ruta_pdf):
        return None
        
    loader = PyPDFLoader(ruta_pdf)
    docs = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(loader.load())
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    return FAISS.from_documents(docs, embeddings)

def buscar_en_manual(vector_db, consulta):
    """Busca las reglas de APA 7 relevantes para el error detectado."""
    if not vector_db:
        return ""
    docs = vector_db.similarity_search(consulta, k=3)
    return "\n\n".join([d.page_content for d in docs])
