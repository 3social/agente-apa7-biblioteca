import streamlit as st
import docx
import io
import os
from openai import OpenAI
from dotenv import load_dotenv

# ✅ SIEMPRE debe ser la primera llamada a Streamlit
st.set_page_config(page_title="Agente APA 7 - Biblioteca", page_icon="📚", layout="wide")

# Cargar .env solo en local
load_dotenv()

# ✅ Leer key con fallback local
API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not API_KEY:
    st.error("⚠️ No se encontró la API KEY.")
    st.info("En Streamlit Cloud: Settings → Secrets → agrega OPENAI_API_KEY")
    st.stop()

# --- UI ---
st.title("📚 Plataforma de Revisión APA 7")
st.info("Sube el trabajo del alumno. El sistema validará la coherencia entre citas y referencias automáticamente.")

# --- LÓGICA ---
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
            if not t:
                continue
            if t.lower().replace(":", "") in marcas:
                en_refs = True
                continue
            if en_refs:
                refs.append(t)
            else:
                cuerpo.append(t)
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
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"CUERPO:\n{cuerpo}\n\nREFS:\n{refs}"}
            ]
        )
        return response.choices[0].message.content

# --- INTERFAZ ---
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