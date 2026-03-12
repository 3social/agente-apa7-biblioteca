# 📚 Agente de Revisión APA 7 - Plataforma de Biblioteca
> **Solución Inteligente para la Validación de Coherencia y Formato Académico.**

Esta plataforma automatiza la revisión bibliográfica en bibliotecas universitarias, utilizando Inteligencia Artificial (**OpenAI GPT-4o-mini**) para garantizar la integridad entre las citas en el texto y la lista de referencias, cumpliendo estrictamente con el **Manual APA 7ma Edición**.

---

## ✨ Características Principales
- **🔍 Validación de Coherencia Cruzada:** Detecta automáticamente citas huérfanas (en texto pero no en referencias) y fuentes sobrantes (en referencias pero no citadas).
- **📝 Análisis de Formato Estructural:** Revisa el uso de cursivas en títulos, aplicación de sangría francesa y el orden alfabético riguroso de la bibliografía.
- **📥 Reportes Descargables:** Genera un archivo `.docx` con retroalimentación pedagógica detallada para el estudiante.
- **🌐 Interfaz Web Moderna:** Desplegado en la nube para un acceso fácil desde cualquier navegador, sin necesidad de instalar software adicional.

---

## 🛠️ Stack Tecnológico
- **Frontend/Backend:** [Streamlit](https://streamlit.io/ ) (Python-based Web Framework)
- **Procesamiento de Documentos:** `python-docx`
- **Motor de IA:** OpenAI API (Modelos GPT-4o-mini)
- **Seguridad:** Gestión de credenciales mediante Variables de Entorno y Secrets.

---

## 🚀 Guía de Uso Rápido

### 1. Acceso a la Plataforma
Accede a la URL pública de la aplicación (proporcionada por Streamlit Cloud).

### 2. Carga de Documento
Arrastra y suelta el archivo del alumno en formato `.docx`. El sistema identificará automáticamente las secciones de "Cuerpo del Texto" y "Referencias".

### 3. Análisis y Descarga
Haz clic en **"Iniciar Análisis Profesional"**. Tras unos segundos, podrás previsualizar el feedback en pantalla y descargar el reporte final en Word para enviarlo al alumno.

---

## 🛡️ Configuración de Seguridad (Para Desarrolladores)
Para replicar este proyecto o desplegarlo en un nuevo entorno:
1. Crea un archivo `.env` en la raíz con tu `OPENAI_API_KEY`.
2. En **Streamlit Cloud**, configura la clave en `Settings > Secrets` usando el formato:
   ```toml
   OPENAI_API_KEY = "sk-proj-..."

   ## Copyright

© 2026 Michael González. All rights reserved.

This software is protected by copyright law.
Unauthorized reproduction or distribution is prohibited.
