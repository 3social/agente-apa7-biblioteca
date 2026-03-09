# 📚 Agente de Revisión APA 7 - Automatización para Bibliotecas
> Una solución inteligente para la validación de coherencia en citas y referencias académicas.

Este proyecto nace de la necesidad de optimizar la labor de revisión bibliográfica en bibliotecas universitarias. Utiliza Inteligencia Artificial (OpenAI GPT-4o-mini) para detectar discrepancias entre las citas en el texto y la lista de referencias final, asegurando el cumplimiento estricto del **Manual APA 7ma Edición**.

---

## ✨ Características Principales
- **🔍 Validación de Coherencia Cruzada:** Identifica citas en el texto que no aparecen en las referencias (citas huérfanas) y fuentes listadas que nunca fueron citadas (referencias sobrantes).
- **📝 Análisis de Formato Estructural:** Revisa automáticamente el uso de cursivas en títulos, la aplicación de la sangría francesa y el orden alfabético riguroso.
- **📥 Generación de Reportes:** Crea un documento de retroalimentación en formato `.docx` listo para ser entregado al estudiante con sugerencias de corrección pedagógicas.
- **🛡️ Privacidad y Seguridad:** Implementación segura mediante variables de entorno (`.env`) para proteger las credenciales de API.

---

## 🛠️ Tecnologías Utilizadas
- **Lenguaje:** Python 3.10+
- **Interfaz (UI):** [Streamlit](https://streamlit.io/ )
- **Procesamiento de Documentos:** `python-docx`
- **Cerebro de IA:** OpenAI API (Modelos GPT)

---

## 🚀 Instalación y Uso Local

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/agente-apa7-biblioteca.git
   cd agente-apa7-biblioteca
