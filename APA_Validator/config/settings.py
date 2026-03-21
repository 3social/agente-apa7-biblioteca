"""
Configuración central del sistema.

Orden de prioridad (mayor a menor):
  1. Streamlit Secrets  — producción en la nube (importado solo si está disponible)
  2. Variables de entorno / .env — desarrollo local
  3. None — el caller decide cómo manejar la ausencia
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get(key: str) -> str | None:
    """Lee una clave desde Streamlit Secrets o variables de entorno."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key) or None


class Settings:
    def __init__(self):
        self.OPENAI_API_KEY:      str | None = _get("OPENAI_API_KEY")
        self.SUPABASE_URL:        str | None = _get("SUPABASE_URL")
        # Anon key — para operaciones de Auth (OTP, sesiones) desde el frontend.
        self.SUPABASE_KEY:        str | None = _get("SUPABASE_KEY")
        # Service role key — bypasea RLS, solo para el backend (analytics, inserts).
        self.SUPABASE_SERVICE_KEY: str | None = _get("SUPABASE_SERVICE_KEY")
        # UUID de la universidad activa en este deployment.
        self.UNIVERSITY_ID:       str | None = _get("UNIVERSITY_ID")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MANUAL_PDF_PATH: str = os.path.join(base_dir, "manual_apa7.pdf")


settings = Settings()
