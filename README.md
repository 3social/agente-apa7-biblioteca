# 📚 Agente de Revisión APA 7 - Ecosistema Modular de Biblioteca
> **Plataforma Profesional de Revisión Académica con Arquitectura Modular, IA y RAG.**

Este ecosistema automatiza la revisión bibliográfica en bibliotecas universitarias, integrando **Inteligencia Artificial de vanguardia** con una **Base de Conocimiento propia** y un sistema de **Memoria Institucional** para la toma de decisiones pedagógicas, bajo una estructura de software escalable.

---

## 🏗️ Arquitectura Modular del Sistema
El proyecto sigue el estándar de **Separación de Responsabilidades**, lo que permite un mantenimiento sencillo y una alta escalabilidad:

- **`app.py`**: Orquestador principal de la interfaz de usuario (Streamlit).
- **`config/settings.py`**: Gestión centralizada de configuraciones y seguridad (API Keys).
- **`modules/`**:
  - `citation_extractor.py`: Lógica de extracción de contenido desde archivos `.docx`.
  - `apa_validator.py`: Cerebro de IA que valida el cumplimiento de normas APA 7.
  - `analytics.py`: Conector con **Supabase** para el Feedback Loop institucional.
- **`rag/knowledge_base.py`**: Motor de búsqueda semántica en el manual oficial PDF (LangChain + FAISS).
- **`reports/report_generator.py`**: Generación automatizada de reportes de feedback en formato Word.

---

## ✨ Características de Nivel Ingeniería
- **🔍 Validación de Coherencia Cruzada:** Motor que detecta discrepancias entre citas en el texto y la lista de referencias.
- **🧠 Motor RAG (Retrieval-Augmented Generation):** El agente consulta en tiempo real el **Manual Oficial de APA 7ma Edición (PDF)** antes de emitir cada corrección.
- **📊 Memoria Institucional (Supabase):** Registro histórico de errores frecuentes para generar analítica de apoyo docente.
- **🛡️ Seguridad Industrial:** Manejo de credenciales mediante variables de entorno (`.env`) y Secrets en la nube.

---

## 🛠️ Stack Tecnológico
- **Frontend/UI:** [Streamlit](https://streamlit.io/ )
- **Cerebro de IA:** OpenAI API (GPT-4o-mini)
- **Orquestador RAG:** [LangChain](https://www.langchain.com/ )
- **Base de Datos:** [Supabase](https://supabase.com/ ) (PostgreSQL)
- **Procesamiento de Documentos:** `python-docx` y `pypdf`

---

   ## Copyright

© 2026 Michael González. All rights reserved.

This software is protected by copyright law.
Unauthorized reproduction or distribution is prohibited.
