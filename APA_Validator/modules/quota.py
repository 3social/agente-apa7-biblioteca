"""
Gestión de cuotas por plan — Fase 11.2
========================================
Controla el uso mensual de análisis por universidad.

Planes:
  basico        → 100 documentos / mes
  profesional   → 500 documentos / mes
  institucional → sin límite
"""

from __future__ import annotations

from dataclasses import dataclass

from supabase import create_client


# ── Límites por plan ──────────────────────────────────────────────────────────

_LIMITES: dict[str, int | None] = {
    "basico":        100,
    "profesional":   500,
    "institucional": None,   # sin límite
}

_UMBRAL_AVISO = 0.80   # aviso al llegar al 80% del límite


# ── Modelo ────────────────────────────────────────────────────────────────────

@dataclass
class EstadoCuota:
    usados:      int
    limite:      int | None   # None = sin límite
    plan_tier:   str

    @property
    def porcentaje(self) -> float:
        if not self.limite:
            return 0.0
        return self.usados / self.limite

    @property
    def bloqueado(self) -> bool:
        """True si se alcanzó el 100% del límite."""
        return self.limite is not None and self.usados >= self.limite

    @property
    def aviso(self) -> bool:
        """True si se alcanzó el umbral de aviso (80%) sin estar bloqueado."""
        return not self.bloqueado and self.porcentaje >= _UMBRAL_AVISO

    @property
    def mensaje(self) -> str | None:
        if self.bloqueado:
            return (
                f"Has alcanzado el límite de {self.limite} análisis este mes "
                f"(plan {self.plan_tier}). Contacta a soporte para ampliar tu cuota."
            )
        if self.aviso:
            restantes = self.limite - self.usados
            return (
                f"Has usado {self.usados} de {self.limite} análisis este mes. "
                f"Te quedan {restantes} disponibles (plan {self.plan_tier})."
            )
        return None


# ── Consulta ──────────────────────────────────────────────────────────────────

def verificar_cuota(
    university_id: str,
    supabase_url:  str,
    supabase_key:  str,
) -> EstadoCuota:
    """
    Consulta el uso mensual de la universidad y retorna su estado de cuota.
    Si Supabase no está disponible, retorna cuota sin límite (no bloquea).
    """
    try:
        client = create_client(supabase_url, supabase_key)

        # Obtener plan de la universidad
        univ = (
            client.table("universities")
            .select("plan_tier")
            .eq("id", university_id)
            .single()
            .execute()
        )
        plan_tier = univ.data.get("plan_tier", "basico") if univ.data else "basico"
        limite    = _LIMITES.get(plan_tier)

        if limite is None:
            return EstadoCuota(usados=0, limite=None, plan_tier=plan_tier)

        # Contar documentos del mes actual
        from datetime import datetime, timezone
        inicio_mes = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        conteo = (
            client.table("documents")
            .select("id", count="exact")
            .eq("university_id", university_id)
            .gte("uploaded_at", inicio_mes)
            .execute()
        )
        usados = conteo.count or 0

        return EstadoCuota(usados=usados, limite=limite, plan_tier=plan_tier)

    except Exception:
        # Si falla la consulta, no bloqueamos — permitir el análisis
        return EstadoCuota(usados=0, limite=None, plan_tier="basico")
