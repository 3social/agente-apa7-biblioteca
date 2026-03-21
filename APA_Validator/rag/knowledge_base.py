"""
Base de conocimiento RAG sobre el Manual APA 7.

Indexa el PDF completo del manual (todas las secciones, no solo referencias).
Las búsquedas son dirigidas por sección: cada módulo obtiene el contexto
relevante para lo que valida, evitando queries genéricas que siempre
recuperan los mismos chunks de citas.

Las secciones se consultan solo si:
  a) El documento tiene contenido en esa sección (el extractor la detectó).
  b) El feature flag correspondiente está activo.
Esto reduce el costo de tokens y el ruido en el contexto del LLM.
"""

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from modules.schemas import DocumentoAPA


# Queries optimizadas por sección del Manual APA 7.
# Cada query está diseñada para recuperar los chunks más relevantes
# de esa sección específica del manual.
_QUERIES_SECCION: dict[str, str] = {
    "portada": (
        "página de título portada formato autor institución afiliación "
        "nombre curso instructor fecha APA 7 sección 2"
    ),
    "abstract": (
        "resumen abstract formato longitud máximo 250 palabras "
        "palabras clave keywords sangría APA 7 sección 3"
    ),
    "encabezados": (
        "niveles de encabezado H1 H2 H3 H4 H5 formato centrado "
        "negrita cursiva sangría APA 7 sección 2.27"
    ),
    "cuerpo": (
        "formato cuerpo texto párrafos sangría primera línea "
        "interlineado doble márgenes fuente APA 7 sección 2"
    ),
    "tablas": (
        "tablas formato número título nota tabla datos "
        "presentación APA 7 sección 7 capítulo 7"
    ),
    "figuras": (
        "figuras imágenes gráficos formato nota leyenda número "
        "figura descripción APA 7 sección 7 capítulo 7"
    ),
    "referencias": (
        "lista de referencias bibliografía formato citas orden "
        "alfabético sangría francesa DOI URL APA 7 sección 9"
    ),
    "apendices": (
        "apéndices apéndice formato ubicación contenido material "
        "suplementario etiqueta APA 7 sección 2.14"
    ),
}


# Caché en memoria: evita reconstruir el índice en cada request.
# Clave: primeros 8 chars del api_key (no almacenar la key completa).
_cache: dict[str, object] = {}


def inicializar_conocimiento(ruta_pdf: str, api_key: str):
    """
    Carga el PDF del Manual APA 7 y construye el índice vectorial FAISS.

    Usa caché en memoria para no reconstruir el índice en cada request.
    Compatible con Streamlit y con FastAPI (sin dependencias de st.*).
    chunk_overlap=200 mejora la recuperación en secciones limítrofes.
    """
    if not os.path.exists(ruta_pdf):
        return None

    cache_key = f"{ruta_pdf}:{api_key[:8]}"
    if cache_key in _cache:
        return _cache[cache_key]

    loader = PyPDFLoader(ruta_pdf)
    docs = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    ).split_documents(loader.load())

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    vector_db = FAISS.from_documents(docs, embeddings)

    _cache[cache_key] = vector_db
    return vector_db


def buscar_en_manual(vector_db, consulta: str, k: int = 3) -> str:
    """
    Búsqueda simple sobre el índice vectorial.
    Mantiene compatibilidad con el flujo básico (validacion_citas).
    """
    if not vector_db:
        return ""
    docs = vector_db.similarity_search(consulta, k=k)
    return "\n\n".join(d.page_content for d in docs)


def buscar_contexto_completo(vector_db, documento: DocumentoAPA, features) -> dict[str, str]:
    """
    Retorna un dict {seccion: contexto_del_manual} consultando solo
    las secciones que tienen contenido Y cuyo feature flag está activo.

    Lógica de activación por sección:
      - referencias:  siempre (core, feature validacion_citas).
      - portada/abstract/encabezados/tablas/figuras/apendices:
            requiere features.extractor_completo.
      - cuerpo (formato físico): requiere features.validacion_formato.

    Retorna strings vacíos para secciones sin contexto, lo que el LLM
    interpreta correctamente como "no hay reglas adicionales para esto".
    """
    if not vector_db:
        return {}

    secciones: dict[str, str] = {}

    # ── Core: siempre activo ─────────────────────────────────────────────────
    if documento.referencias:
        secciones["referencias"] = _QUERIES_SECCION["referencias"]

    # ── Extractor completo (Fase 0.2) ────────────────────────────────────────
    if features.extractor_completo:
        if documento.portada:
            secciones["portada"] = _QUERIES_SECCION["portada"]
        if documento.abstract:
            secciones["abstract"] = _QUERIES_SECCION["abstract"]
        if documento.encabezados:
            secciones["encabezados"] = _QUERIES_SECCION["encabezados"]
        if documento.tablas:
            secciones["tablas"] = _QUERIES_SECCION["tablas"]
        if documento.figuras:
            secciones["figuras"] = _QUERIES_SECCION["figuras"]
        if documento.apendices:
            secciones["apendices"] = _QUERIES_SECCION["apendices"]

    # ── Validación de formato físico (Fase 0.3) ──────────────────────────────
    if features.validacion_formato and documento.cuerpo:
        secciones["cuerpo"] = _QUERIES_SECCION["cuerpo"]

    if not secciones:
        return {}

    # Ejecutar búsquedas — una por sección activa.
    return {
        seccion: buscar_en_manual(vector_db, query, k=3)
        for seccion, query in secciones.items()
    }
