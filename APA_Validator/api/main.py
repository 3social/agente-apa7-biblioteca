"""
API REST — Fase 9.2
===================
Expone el Core Engine como API HTTP.

Endpoints:
  POST /analyze          — Recibe un .docx, retorna análisis APA completo.
  GET  /health           — Estado del servicio y disponibilidad del manual.

Streamlit (app.py) es ahora un cliente más de esta API.
En Fase 10 se agregarán /metrics/{university_id} y /universities
junto con autenticación JWT por tenant.

Ejecutar en desarrollo:
  uvicorn api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.engine import EngineConfig, analizar_documento
from modules.schemas import AnalisisAPA
from rag.knowledge_base import inicializar_conocimiento


# ── Lifespan: inicializar conocimiento una sola vez al arrancar ───────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-carga el índice vectorial en memoria antes de recibir requests.
    # Si el PDF no existe, la API funciona igual pero sin contexto del manual.
    if settings.OPENAI_API_KEY:
        inicializar_conocimiento(settings.MANUAL_PDF_PATH, settings.OPENAI_API_KEY)
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agente APA 7 — API",
    version="0.9.0",
    description="Motor de validación APA 7 para plataformas universitarias.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Fase 10: restringir a dominios universitarios autorizados
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health():
    """Estado del servicio."""
    import os
    return {
        "status":       "ok",
        "version":      "0.9.0",
        "openai_key":   bool(settings.OPENAI_API_KEY),
        "supabase":     bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
        "manual_apa7":  os.path.exists(settings.MANUAL_PDF_PATH),
    }


@app.post(
    "/analyze",
    response_model=AnalisisAPA,
    tags=["Análisis"],
    summary="Analiza un documento .docx contra las normas APA 7",
)
async def analyze(
    file: UploadFile = File(..., description="Archivo .docx del trabajo académico"),
):
    """
    Recibe un archivo `.docx` y retorna el análisis APA 7 completo.

    Incluye:
    - Errores de citas y referencias (siempre activo)
    - Errores de formato físico (si FEATURE_VALIDACION_FORMATO=true)
    - Observaciones de estilo académico (si FEATURE_ESTILO_ACADEMICO=true)
    """
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(
            status_code=415,
            detail="Solo se aceptan archivos .docx",
        )

    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY no configurada en el servidor.",
        )

    docx_bytes = await file.read()

    try:
        analisis = analizar_documento(
            docx_bytes=docx_bytes,
            nombre_archivo=file.filename,
            config=EngineConfig(),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

    return analisis
