import streamlit as st
import docx
import io
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Cargar .env solo para local
load_dotenv()

# Buscar la clave en Streamlit Secrets O en variables de entorno
# Nota: Streamlit Cloud prioriza st.secrets
API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# --- VERIFICACIÓN DE SEGURIDAD ---
if not API_KEY:
    st.error("⚠️ Error de Configuración: No se encontró la API KEY.")
    st.info("Si estás en Streamlit Cloud, asegúrate de haberla puesto en 'Settings > Secrets'.")
    st.stop() # Detiene la ejecución de forma limpia

# --- CONFIGURACIÓN DE UI ---
st.set_page_config(page_title="Agente APA 7 - Biblioteca", page_icon="📚", layout="wide")

st.title("📚 Plataforma de Revisión APA 7")
st.info("Sube el trabajo del alumno. El sistema validará la coherencia entre citas y referencias automáticamente.")

# --- LÓGICA DE NEGOCIO (PROFESIONAL) ---
class AgenteAPA:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def extraer_secciones(self, file_bytes):
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

    def analizar(self, cuerpo, refs):
        prompt = (
            "Eres un bibliotecario experto en APA 7. Genera un REPORTE ESTRUCTURADO:\n"
            "1. VALIDACIÓN DE COHERENCIA: Citas en texto vs Referencias.\n"
            "2. FORMATO APA 7: Cursivas, sangría, orden alfabético.\n"
            "3. EJEMPLOS DE CORRECCIÓN."
        )
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt},
                      {"role": "user", "content": f"CUERPO:\n{cuerpo}\n\nREFS:\n{refs}"}]
        )
        return response.choices[0].message.content

# --- INTERFAZ ---
if not API_KEY:
    st.error("❌ Error: No se encontró la API KEY en el archivo .env")
else:
    agente = AgenteAPA(API_KEY)
    archivo = st.file_uploader("Selecciona el archivo .docx", type=["docx"])

    if archivo:
        if st.button("🚀 Analizar Documento"):
            with st.spinner("Procesando..."):
                cuerpo, refs = agente.extraer_secciones(archivo.read())
                reporte_texto = agente.analizar(cuerpo, refs)
                
                st.success("¡Análisis Finalizado!")
                st.markdown("### Vista Previa del Reporte")
                st.markdown(reporte_texto)
                
                # Generar archivo de descarga
                output = io.BytesIO()
                doc_out = docx.Document()
                doc_out.add_heading(f"Reporte APA - {archivo.name}", 0)
                for line in reporte_texto.split('\n'):
                    doc_out.add_paragraph(line)
                doc_out.save(output)
                
                st.download_button(
                    label="📥 Descargar Reporte Word",
                    data=output.getvalue(),
                    file_name=f"Feedback_APA_{archivo.name}",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
