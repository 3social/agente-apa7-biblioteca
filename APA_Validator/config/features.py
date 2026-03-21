"""
Sistema de Feature Flags del Agente APA 7.

Controla qué funcionalidades están activas sin tocar código.
Las flags se leen desde variables de entorno o Streamlit Secrets,
lo que permite habilitarlas por universidad o por ambiente (local, staging, prod)
sin hacer un nuevo deploy.

Orden de prioridad (mayor a menor):
  1. Streamlit Secrets (producción en la nube)
  2. Variables de entorno / archivo .env (desarrollo local)
  3. Valor por defecto definido aquí

Agregar una feature nueva:
  1. Declarar el campo en FeatureFlags con default=False.
  2. Agregar la entrada en _DEFAULTS con su nombre de env var.
  3. Listo — el sistema la carga automáticamente.
"""

import os
from dataclasses import dataclass, fields


@dataclass
class FeatureFlags:
    # ── Core ──────────────────────────────────────────────────────────────────
    # Fase 0.1 — siempre activo, no se puede apagar.
    validacion_citas: bool = True

    # ── Fase 0.2 ──────────────────────────────────────────────────────────────
    # Extractor completo: portada, abstract, encabezados H1-H5,
    # tablas, figuras, apéndices.
    extractor_completo: bool = False

    # ── Fase 0.3 ──────────────────────────────────────────────────────────────
    # Validación de formato físico: márgenes, fuente, interlineado, sangría.
    validacion_formato: bool = False

    # ── Fase 0.4 ──────────────────────────────────────────────────────────────
    # Estilo académico APA 7: lenguaje sin sesgo, registro formal, primera
    # persona, afirmaciones sin respaldo, verbosidad. Opcional — default False.
    estilo_academico: bool = False


    def activas(self) -> list[str]:
        """Retorna los nombres de las features actualmente habilitadas."""
        return [f.name for f in fields(self) if getattr(self, f.name)]

    def resumen_sidebar(self) -> dict[str, str]:
        """
        Retorna un dict {nombre: estado} con íconos para mostrar
        en el sidebar de Streamlit.
        """
        return {
            f.name: ("✅" if getattr(self, f.name) else "⬜")
            for f in fields(self)
        }


# Mapa de field_name → nombre de la variable de entorno correspondiente.
_ENV_VARS: dict[str, str] = {
    "validacion_citas":    "FEATURE_VALIDACION_CITAS",
    "extractor_completo":  "FEATURE_EXTRACTOR_COMPLETO",
    "validacion_formato":  "FEATURE_VALIDACION_FORMATO",
    "estilo_academico":    "FEATURE_ESTILO_ACADEMICO",
}


def _leer_bool(env_var: str, default: bool) -> bool:
    """
    Lee un booleano desde Streamlit Secrets o variables de entorno.
    Acepta: 1, true, yes, on → True | 0, false, no, off → False.
    """
    # 1. Streamlit Secrets (nube)
    try:
        import streamlit as st
        val = st.secrets.get(env_var)
        if val is not None:
            return str(val).lower().strip() in ("1", "true", "yes", "on")
    except Exception:
        pass

    # 2. Variable de entorno / .env
    val = os.getenv(env_var, "").lower().strip()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False

    # 3. Valor por defecto
    return default


def _cargar_features() -> FeatureFlags:
    base = FeatureFlags()
    kwargs = {}
    for field_name, env_var in _ENV_VARS.items():
        default = getattr(base, field_name)
        kwargs[field_name] = _leer_bool(env_var, default)

    # validacion_citas es siempre True — no se puede apagar desde el exterior.
    kwargs["validacion_citas"] = True

    return FeatureFlags(**kwargs)


# Instancia global — importar desde aquí en todos los módulos.
features = _cargar_features()
