import os
import streamlit as st
from dotenv import load_dotenv

# 1. Intentar cargar el archivo .env (Local)
load_dotenv()

class Settings:
    def __init__(self):
        # 2. Intentar obtener las claves de Streamlit Secrets (Nube)
        # Usamos un bloque try/except para que no falle en Local si no hay secrets
        try:
            self.OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
            self.SUPABASE_URL = st.secrets.get("SUPABASE_URL")
            self.SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
        except:
            # Si falla (estamos en Local), las ponemos como None para buscarlas en el .env
            self.OPENAI_API_KEY = None
            self.SUPABASE_URL = None
            self.SUPABASE_KEY = None

        # 3. Si no están en Secrets, buscarlas en el archivo .env (os.getenv)
        self.OPENAI_API_KEY = self.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.SUPABASE_URL = self.SUPABASE_URL or os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = self.SUPABASE_KEY or os.getenv("SUPABASE_KEY")
        
        # Ruta del manual
        self.MANUAL_PDF_PATH = "manual_apa7.pdf"

# Crear la instancia de configuración
settings = Settings()

# --- VALIDACIÓN DE SEGURIDAD PARA LA TERMINAL ---
if not settings.OPENAI_API_KEY:
    print("❌ ERROR: No se encontró la OPENAI_API_KEY en .env ni en Secrets.")
