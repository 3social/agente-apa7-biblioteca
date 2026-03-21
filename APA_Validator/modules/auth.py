"""
Fase 10.3 — Autenticación por dominio universitario.

Flujo OTP:
  1. Usuario ingresa email institucional.
  2. Sistema valida que el dominio está autorizado en universities.
  3. Supabase envía código de 6 dígitos al email.
  4. Usuario ingresa el código → sesión activa.
  5. university_id se extrae del JWT (app_metadata) para RLS y analítica.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from supabase import Client, create_client


# ── Modelo de sesión ──────────────────────────────────────────────────────────

@dataclass
class SesionUsuario:
    email:          str
    university_id:  str
    university_name: str
    access_token:   str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cliente_anon(supabase_url: str, supabase_key: str) -> Client:
    return create_client(supabase_url, supabase_key)


def validar_dominio(
    email:          str,
    supabase_url:   str,
    supabase_key:   str,
) -> Optional[dict]:
    """
    Verifica que el dominio del email esté autorizado en universities.

    Returns:
        dict con {id, name} de la universidad, o None si no está autorizado.
    """
    dominio = email.split("@")[-1].lower().strip() if "@" in email else ""
    if not dominio:
        return None

    try:
        client = _cliente_anon(supabase_url, supabase_key)
        # Busca universidad con dominio vacío (demo) o que incluya este dominio
        response = client.table("universities").select("id, name, authorized_domains").eq("active", True).execute()

        for universidad in response.data:
            dominios = universidad.get("authorized_domains") or []
            if not dominios or dominio in dominios:
                return {"id": universidad["id"], "name": universidad["name"]}
    except Exception:
        pass

    return None


def enviar_otp(
    email:        str,
    supabase_url: str,
    supabase_key: str,
) -> bool:
    """
    Envía un código OTP al email del usuario vía Supabase Auth.

    Returns:
        True si el envío fue exitoso, False si hubo error.
    """
    try:
        client = _cliente_anon(supabase_url, supabase_key)
        client.auth.sign_in_with_otp({"email": email})
        return True
    except Exception:
        return False


def verificar_otp(
    email:        str,
    token:        str,
    supabase_url: str,
    supabase_key: str,
) -> Optional[SesionUsuario]:
    """
    Verifica el código OTP y retorna la sesión del usuario.

    Returns:
        SesionUsuario con university_id del JWT, o None si el código es inválido.
    """
    try:
        client = _cliente_anon(supabase_url, supabase_key)
        response = client.auth.verify_otp({
            "email": email,
            "token": token.strip(),
            "type":  "email",
        })

        session = response.session
        if not session:
            return None

        # Extraer university_id del JWT (inyectado por custom_access_token_hook)
        university_id = (
            session.user.app_metadata.get("university_id")
            if session.user and session.user.app_metadata
            else None
        )

        if not university_id:
            # Fallback: buscar por dominio del email (si el hook aún no está activo)
            universidad = validar_dominio(email, supabase_url, supabase_key)
            university_id = universidad["id"] if universidad else None

        return SesionUsuario(
            email=email,
            university_id=university_id or "",
            university_name="",
            access_token=session.access_token,
        )

    except Exception:
        return None


def cerrar_sesion(supabase_url: str, supabase_key: str) -> None:
    """Cierra la sesión activa en Supabase."""
    try:
        client = _cliente_anon(supabase_url, supabase_key)
        client.auth.sign_out()
    except Exception:
        pass
