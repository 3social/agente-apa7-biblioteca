# 📚 Agente de Revisión APA 7 - Ecosistema Inteligente de Biblioteca
> **Plataforma Avanzada de Revisión Académica con IA, RAG y Analítica en Tiempo Real.**

Este ecosistema automatiza la revisión bibliográfica en bibliotecas universitarias, integrando **Inteligencia Artificial de vanguardia** con una **Base de Conocimiento propia** y un sistema de **Memoria Institucional** para la toma de decisiones pedagógicas.

---

## 🚀 Capacidades de Nivel Profesional
- **🔍 Validación de Coherencia Cruzada:** Motor lógico que detecta discrepancias exactas entre citas en el texto y la lista de referencias final.
- **🧠 Motor RAG (LangChain + FAISS):** El agente consulta en tiempo real el **Manual Oficial de APA 7ma Edición (PDF)** antes de emitir cada corrección, garantizando respuestas con autoridad bibliotecaria.
- **📊 Memoria Institucional (Supabase):** Registro automático de cada revisión en una base de datos PostgreSQL. Permite identificar los errores más comunes de los estudiantes para diseñar talleres de refuerzo.
- **📝 Generación de Feedback Pedagógico:** Creación de reportes en formato `.docx` listos para descargar y entregar al alumno con sugerencias de mejora.

---

## 🛠️ Stack Tecnológico
- **Frontend/UI:** [Streamlit](https://streamlit.io/ ) (Framework Web de alto rendimiento para Python).
- **Cerebro de IA:** OpenAI API (Modelos GPT-4o-mini).
- **Orquestador RAG:** [LangChain](https://www.langchain.com/ ) para búsqueda semántica en documentos PDF.
- **Base de Datos:** [Supabase](https://supabase.com/ ) (PostgreSQL) para analítica de errores.
- **Procesamiento de Documentos:** `python-docx` y `pypdf`.

---

## ⚙️ Configuración de Seguridad y Despliegue
Este proyecto está diseñado bajo estándares de **GitHub Ready** (seguridad total de credenciales).

### 1. Variables de Entorno (Local)
Crea un archivo `.env` en la raíz con las siguientes claves:
```env
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=eyJ...tu-clave-anon-publica


   ## Copyright

© 2026 Michael González. All rights reserved.

This software is protected by copyright law.
Unauthorized reproduction or distribution is prohibited.
