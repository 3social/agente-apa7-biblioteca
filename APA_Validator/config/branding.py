"""
Branding institucional — Fase 11.1
====================================
Carga la identidad visual de la universidad activa desde Supabase.
Usado en reportes Word y en la interfaz Streamlit.

Colores por defecto (UNA — piloto):
  Rojo   Pantone 185    #DA291C
  Gris   Pantone Cool Gray 6  #A7A8AA
  Azul   Pantone Reflex Blue  #003DA5
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from supabase import create_client


# ── Modelo ────────────────────────────────────────────────────────────────────

@dataclass
class BrandingUniversidad:
    nombre:           str   = "Universidad"
    color_primario:   str   = "#DA291C"    # Rojo Pantone 185
    color_secundario: str   = "#A7A8AA"    # Gris Pantone Cool Gray 6
    color_acento:     str   = "#003DA5"    # Azul Pantone Reflex Blue
    logo_path:        str | None = None    # Ruta local al PNG del logo

    @property
    def logo_existe(self) -> bool:
        return self.logo_path is not None and os.path.exists(self.logo_path)

    def color_primario_rgb(self) -> tuple[int, int, int]:
        """Convierte color_primario hex a (R, G, B) para python-docx."""
        c = self.color_primario.lstrip("#")
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


# ── Caché en memoria ──────────────────────────────────────────────────────────

_cache: dict[str, BrandingUniversidad] = {}

# Ruta base para logos locales
_LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logos")


def cargar_branding(
    university_id: str | None,
    supabase_url:  str | None,
    supabase_key:  str | None,
) -> BrandingUniversidad:
    """
    Carga el branding de la universidad desde Supabase.
    Si no se puede conectar o el ID es None, retorna los defaults del piloto.
    """
    if not university_id:
        return BrandingUniversidad()

    if university_id in _cache:
        return _cache[university_id]

    branding = BrandingUniversidad()   # defaults

    if supabase_url and supabase_key:
        try:
            client = create_client(supabase_url, supabase_key)
            response = (
                client.table("universities")
                .select("name, primary_color")
                .eq("id", university_id)
                .single()
                .execute()
            )
            data = response.data
            if data:
                branding.nombre         = data.get("name", branding.nombre)
                branding.color_primario = data.get("primary_color") or branding.color_primario
        except Exception:
            pass

    # Buscar logo local con UUID con guiones o sin ellos
    uuid_sin_guiones = university_id.replace("-", "")
    for nombre in (f"{university_id}.png", f"{uuid_sin_guiones}.png"):
        candidato = os.path.join(_LOGOS_DIR, nombre)
        if os.path.exists(candidato):
            branding.logo_path = candidato
            break

    _cache[university_id] = branding
    return branding
