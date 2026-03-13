from supabase import Client, create_client
import streamlit as st

def guardar_metrica_revision(supabase_url, supabase_key, nombre_archivo, feedback):
    """Guarda los datos de la revisión en Supabase para analítica institucional."""
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Lógica de detección simple de errores en el texto
        data = {
            "alumno": nombre_archivo,
            "citas_huerfanas": 1 if "huérfana" in feedback.lower() else 0,
            "refs_sobrantes": 1 if "sobrante" in feedback.lower() else 0,
            "error_mas_comun": "Formato" if "sangría" in feedback.lower() else "Coherencia"
        }
        
        supabase.table("revisiones_apa").insert(data).execute()
        return True
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error al guardar analítica: {e}")
        return False
