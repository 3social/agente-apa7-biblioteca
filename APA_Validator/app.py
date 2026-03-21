"""
APA Validator AI — Interfaz Streamlit
======================================
Cliente visual del Core Engine con autenticación por dominio universitario.

Copyright (c) 2026 Michael González
All rights reserved.
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.branding import cargar_branding
from config.settings import settings
from config.features import features
from core.engine import EngineConfig, analizar_documento
from modules.auth import SesionUsuario, cerrar_sesion, enviar_otp, validar_dominio, verificar_otp
from modules.quota import verificar_cuota
from modules.schemas import Severidad
from rag.knowledge_base import inicializar_conocimiento
from reports.report_generator import generar_reporte_docx


# ── Configuración de la interfaz ──────────────────────────────────────────────

st.set_page_config(
    page_title="Agente APA 7 - Biblioteca",
    page_icon="📚",
    layout="centered",
)


# ── Auth: flujo de login ──────────────────────────────────────────────────────

def _pantalla_login() -> None:
    """Pantalla de inicio de sesión con OTP por email institucional."""
    st.title("📚 Agente APA 7")
    st.markdown("### Acceso institucional")
    st.markdown("Ingresa tu correo universitario para continuar.")

    etapa = st.session_state.get("auth_etapa", "email")

    if etapa == "email":
        with st.form("form_email"):
            email = st.text_input("Correo institucional", placeholder="usuario@universidad.edu")
            enviado = st.form_submit_button("Continuar")

        if enviado and email:
            # 1. Validar dominio
            universidad = validar_dominio(email, settings.SUPABASE_URL, settings.SUPABASE_KEY)
            if not universidad:
                st.error("Este correo no pertenece a una institución registrada.")
                return

            # 2. Enviar OTP
            if enviar_otp(email, settings.SUPABASE_URL, settings.SUPABASE_KEY):
                st.session_state["auth_etapa"]  = "otp"
                st.session_state["auth_email"]  = email
                st.session_state["auth_univ"]   = universidad
                st.rerun()
            else:
                st.error("No se pudo enviar el código. Intenta de nuevo.")

    elif etapa == "otp":
        email     = st.session_state.get("auth_email", "")
        universidad = st.session_state.get("auth_univ", {})

        st.info(f"Código enviado a **{email}**. Revisa tu bandeja de entrada.")

        with st.form("form_otp"):
            token = st.text_input("Código de verificación (6 dígitos)", max_chars=6)
            verificar = st.form_submit_button("Ingresar")

        if verificar and token:
            sesion = verificar_otp(email, token, settings.SUPABASE_URL, settings.SUPABASE_KEY)
            if sesion:
                # Usar university_id del JWT o el detectado por dominio
                sesion.university_id  = sesion.university_id or universidad.get("id", "")
                sesion.university_name = universidad.get("name", "")
                st.session_state["sesion"]     = sesion
                st.session_state["auth_etapa"] = "autenticado"
                st.rerun()
            else:
                st.error("Código incorrecto o expirado. Intenta de nuevo.")

        if st.button("Usar otro correo"):
            st.session_state.pop("auth_etapa", None)
            st.session_state.pop("auth_email", None)
            st.rerun()


def _obtener_sesion() -> SesionUsuario | None:
    return st.session_state.get("sesion")


# ── Lógica principal ──────────────────────────────────────────────────────────

sesion = _obtener_sesion()

if not sesion:
    _pantalla_login()
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Estado del Sistema")

    if not settings.OPENAI_API_KEY:
        st.error("❌ Falta OpenAI API Key")
        st.stop()

    vector_db = inicializar_conocimiento(settings.MANUAL_PDF_PATH, settings.OPENAI_API_KEY)
    if vector_db:
        st.success("✅ Manual APA 7 Activo")
    else:
        st.warning("⚠️ No se encontró manual_apa7.pdf")

    # Branding institucional
    branding = cargar_branding(sesion.university_id, settings.SUPABASE_URL, settings.SUPABASE_KEY)
    if branding.logo_existe:
        st.image(branding.logo_path, width=120)
    st.markdown(f"**{branding.nombre}**")
    st.caption(f"_{sesion.email}_")

    # Estado de cuota
    if sesion.university_id and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        cuota = verificar_cuota(sesion.university_id, settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        if cuota.limite:
            st.progress(min(cuota.porcentaje, 1.0), text=f"{cuota.usados}/{cuota.limite} análisis este mes")
        if cuota.aviso:
            st.warning(cuota.mensaje)

    st.markdown("---")
    st.caption("**Módulos activos**")
    for nombre, icono in features.resumen_sidebar().items():
        st.caption(f"{icono} {nombre.replace('_', ' ').title()}")

    st.markdown("---")
    if st.button("Cerrar sesión"):
        cerrar_sesion(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        st.session_state.clear()
        st.rerun()


# ── Interfaz principal ────────────────────────────────────────────────────────

st.title("📚 Plataforma Profesional APA 7")
st.markdown("### Automatización y Analítica Institucional")

archivo = st.file_uploader("Sube el trabajo del alumno (.docx)", type=["docx"])

if archivo:
    # Verificar cuota antes de analizar
    cuota = None
    if sesion.university_id and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        cuota = verificar_cuota(sesion.university_id, settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        if cuota.bloqueado:
            st.error(cuota.mensaje)
            st.stop()
        elif cuota.aviso:
            st.warning(cuota.mensaje)

    if st.button("🚀 Iniciar Análisis Profesional"):
        with st.spinner("El Agente está analizando y consultando el manual..."):
            try:
                analisis = analizar_documento(
                    docx_bytes=archivo.read(),
                    nombre_archivo=archivo.name,
                    config=EngineConfig(
                        university_id=sesion.university_id or settings.UNIVERSITY_ID,
                    ),
                )

                # ── Resultados ─────────────────────────────────────────────────

                st.success("¡Análisis Completado!")
                st.markdown("---")

                col1, col2, col3 = st.columns(3)
                col1.metric("Puntaje APA",      f"{analisis.puntaje_apa} / 100")
                col2.metric("Errores críticos",  analisis.resumen.errores_criticos)
                col3.metric("Errores menores",   analisis.resumen.errores_menores)

                st.markdown("---")
                st.markdown(analisis.feedback_texto)

                # Errores de citas y referencias
                if analisis.errores:
                    with st.expander(f"Ver {analisis.resumen.total_errores} errores detallados"):
                        for error in analisis.errores:
                            color = (
                                "🔴" if error.severidad == Severidad.alta  else
                                "🟡" if error.severidad == Severidad.media else
                                "🟢"
                            )
                            st.markdown(
                                f"{color} **{error.tipo.replace('_', ' ').title()}**"
                                f" — _{error.regla_apa}_"
                            )
                            st.caption(f'Fragmento: "{error.fragmento}"')
                            st.info(f"Sugerencia: {error.sugerencia}")

                # Errores de formato físico (Fase 0.3)
                if analisis.errores_formato:
                    st.markdown("---")
                    with st.expander(
                        f"📐 {len(analisis.errores_formato)} errores de formato físico APA 7"
                    ):
                        for ef in analisis.errores_formato:
                            color = (
                                "🔴" if ef["severidad"] == "alta"  else
                                "🟡" if ef["severidad"] == "media" else
                                "🟢"
                            )
                            st.markdown(
                                f"{color} **[{ef['codigo']}] {ef['descripcion']}**"
                                f" — _{ef['regla_apa']}_"
                            )
                            st.caption(
                                f"Encontrado: `{ef['valor_encontrado']}` "
                                f"| Esperado: `{ef['valor_esperado']}`"
                            )
                            st.info(f"Sugerencia: {ef['sugerencia']}")

                # Estilo académico (Fase 0.4)
                if analisis.errores_estilo is not None:
                    st.markdown("---")
                    if analisis.coherencia and analisis.coherencia.get("observacion_estilo"):
                        st.info(analisis.coherencia["observacion_estilo"])
                    label = (
                        f"✍️ {len(analisis.errores_estilo)} observaciones de estilo académico APA 7"
                        if analisis.errores_estilo
                        else "✍️ Estilo académico APA 7 — sin observaciones"
                    )
                    with st.expander(label):
                        if not analisis.errores_estilo:
                            st.success("El texto cumple con el estilo académico APA 7.")
                        for es in analisis.errores_estilo:
                            color = (
                                "🔴" if es["severidad"] == "alta"  else
                                "🟡" if es["severidad"] == "media" else
                                "🟢"
                            )
                            st.markdown(
                                f"{color} **{es['tipo'].replace('_', ' ').title()}**"
                                f" — _{es['capitulo_apa']}_"
                            )
                            st.caption(f'Fragmento: "{es["fragmento"]}"')
                            st.info(f"Sugerencia: {es['sugerencia']}")

                # Descarga del reporte Word con branding institucional
                reporte_word = generar_reporte_docx(
                    analisis.feedback_texto,
                    archivo.name,
                    branding=cargar_branding(sesion.university_id, settings.SUPABASE_URL, settings.SUPABASE_KEY),
                )
                st.download_button(
                    label="📥 Descargar Reporte para el Alumno",
                    data=reporte_word,
                    file_name=f"Reporte_APA_{archivo.name}",
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    ),
                )

            except ValueError as e:
                st.warning(f"⚠️ {e}")
            except Exception as e:
                st.error(f"Error inesperado: {e}")


st.markdown("---")
st.caption("Desarrollado para la optimización de servicios bibliotecarios.")
