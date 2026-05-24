"""
Supervisor 3 — Continuidade e Recuperação (C2M)

Responsabilidades:
  1. Coletar contexto organizacional real a partir de documentos no repositório
  2. Avaliar maturidade organizacional (ISO 22325, modelo Oliva 2016)
  3. Verificar existência de planos (risco, crise, continuidade, recuperação)
  4. Contar eventos similares no histórico (variável H do Monte Carlo)
  5. Calcular score de resiliência

Integra com:
  - DocumentAnalysisService (extração de texto de PDF)
  - GenericsRepository (histórico de eventos do banco)
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Dict, Optional

from src.agents.orchestrator.C2M_Models import OrganizationalContextC2M
from src.api.services.analysis import extract_text
from src.backend.repository.GenericsRepository import get_event_history
from src.core.config.settings import Settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keywords para cada tipo de plano (PT + EN)
# ---------------------------------------------------------------------------
_PLAN_KEYWORDS: Dict[str, list] = {
    "risk": [
        "risco", "risk", "iso 31000", "risk management",
        "gestão de riscos", "gerenciamento de riscos",
    ],
    "crisis": [
        "crise", "crisis", "cyber crisis", "crise cibernética",
        "plano de crise", "crisis management", "iso 22361",
    ],
    "continuity": [
        "continuidade", "continuity", "business continuity",
        "plano de continuidade", "bcp", "iso 22301",
    ],
    "recovery": [
        "recuperação", "recovery", "disaster recovery",
        "plano de recuperação", "drp", "rto", "rpo",
    ],
}

_GOVERNANCE_KEYWORDS = [
    "governança", "governance", "iso 22325", "capability assessment",
    "política de segurança", "security policy", "comitê", "committee",
    "iso 27001",
]

# Tipos de evento considerados "similares" para cálculo de λ (Poisson)
_CYBER_EVENT_TYPES = frozenset({
    "ataque_cibernetico", "ataque", "breach", "ransomware", "malware",
    "falha_sistema", "indisponibilidade", "vazamento", "leak",
    "comprometimento", "violação",
})

# TTL do cache de contexto: 3 600 segundos = 1 hora
_CACHE_TTL_SECONDS = 3_600


class SupervisorContinuityRecovery:
    """
    Agente Supervisor 3 — Continuidade e Recuperação.

    Coleta e devolve um OrganizationalContextC2M que alimenta:
      - a Decision Tree (governança, maturidade)
      - o Monte Carlo (variáveis M, P, H)
    """

    def __init__(self) -> None:
        self.name = "Supervisor Continuidade e Recuperação"
        self.monitors = [
            "Plano de Desastre (DR)",
            "Plano de Continuidade (BC)",
            "Simulações e Testes",
            "Backups e Replicação",
        ]
        self.uploads_dir: Path = Settings.UPLOADS_DIR

        # Cache simples com TTL
        self._cache: Optional[OrganizationalContextC2M] = None
        self._cache_ts: float = 0.0

    # -----------------------------------------------------------------------
    # Ponto de entrada público
    # -----------------------------------------------------------------------

    async def collect_organizational_context(self) -> OrganizationalContextC2M:
        """Coleta (ou retorna do cache) o contexto organizacional."""
        now = time.monotonic()
        if self._cache is not None and (now - self._cache_ts) < _CACHE_TTL_SECONDS:
            log.debug("Supervisor 3: retornando contexto do cache")
            return self._cache

        context = OrganizationalContextC2M(
            maturity_level=await self._extract_maturity_level(),
            has_risk_plan=await self._check_plan_exists("risk"),
            has_crisis_plan=await self._check_plan_exists("crisis"),
            has_continuity_plan=await self._check_plan_exists("continuity"),
            has_recovery_plan=await self._check_plan_exists("recovery"),
            historical_similar_events=self._count_similar_events(),
            formal_governance=await self._check_formal_governance(),
        )

        self._cache = context
        self._cache_ts = now

        log.info(
            "\n"
            "════════════════════════════════════════════════════\n"
            "CONTEXTO ORGANIZACIONAL COLETADO:\n"
            "════════════════════════════════════════════════════\n"
            "  Maturidade:          %.1f / 5.0  (ISO 22325)\n"
            "  Plano de Riscos:     %s\n"
            "  Plano de Crise:      %s\n"
            "  Plano Continuidade:  %s\n"
            "  Plano de Recovery:   %s\n"
            "  Governança Formal:   %s\n"
            "  Eventos similares:   %d  (λ para Poisson)\n"
            "════════════════════════════════════════════════════",
            context.maturity_level,
            "✓" if context.has_risk_plan else "✗",
            "✓" if context.has_crisis_plan else "✗",
            "✓" if context.has_continuity_plan else "✗",
            "✓" if context.has_recovery_plan else "✗",
            "✓" if context.formal_governance else "✗",
            context.historical_similar_events,
        )
        return context

    def invalidate_cache(self) -> None:
        """Força recoleta na próxima chamada (usar após upload de novo documento)."""
        self._cache = None
        self._cache_ts = 0.0

    # -----------------------------------------------------------------------
    # Score de resiliência
    # -----------------------------------------------------------------------

    def assess_resilience(self, context: OrganizationalContextC2M) -> float:
        """
        Score de resiliência ∈ [0, 1]:
          - Existência de planos (40%)
          - Maturidade (40%)
          - Governança formal (20%)
        """
        plans = [
            context.has_risk_plan,
            context.has_crisis_plan,
            context.has_continuity_plan,
            context.has_recovery_plan,
        ]
        plans_score = (sum(plans) / len(plans)) * 0.4
        maturity_score = (context.maturity_level / 5.0) * 0.4
        governance_score = 0.2 if context.formal_governance else 0.0
        return float(min(1.0, plans_score + maturity_score + governance_score))

    # -----------------------------------------------------------------------
    # Implementações privadas
    # -----------------------------------------------------------------------

    async def _extract_maturity_level(self) -> float:
        """
        Extrai maturidade (1–5) de documentos ou infere da presença de planos.

        Prioridade:
          1. Arquivo de modelo de maturidade explícito
          2. Inferência a partir do número de planos encontrados
        """
        maturity_files = [
            "A_maturity_model.pdf",
            "maturity_model.pdf",
            "modelo_maturidade.pdf",
            "capability_assessment.pdf",
        ]

        if self.uploads_dir.exists():
            for fname in maturity_files:
                fpath = self.uploads_dir / fname
                if fpath.exists():
                    text = self._safe_extract_text(fpath)
                    level = self._parse_maturity_from_text(text)
                    if level > 0:
                        log.info("Maturidade extraída de %s: %.1f", fname, level)
                        return level

        # Fallback: inferir da presença de planos
        plan_count = sum([
            await self._check_plan_exists("risk"),
            await self._check_plan_exists("crisis"),
            await self._check_plan_exists("continuity"),
            await self._check_plan_exists("recovery"),
        ])
        inferred = min(5.0, 1.0 + float(plan_count))
        log.info("Maturidade inferida de planos presentes (%d planos): %.1f", plan_count, inferred)
        return inferred

    async def _check_plan_exists(self, plan_type: str) -> bool:
        """Verifica se um tipo de plano está presente nos documentos."""
        keywords = _PLAN_KEYWORDS.get(plan_type, [])
        if not keywords or not self.uploads_dir.exists():
            return False

        for fpath in self.uploads_dir.glob("*"):
            if fpath.suffix.lower() not in {".pdf", ".docx", ".txt", ".doc"}:
                continue
            text = self._safe_extract_text(fpath).lower()
            if any(kw in text for kw in keywords):
                log.debug("Plano '%s' encontrado em: %s", plan_type, fpath.name)
                return True
        return False

    async def _check_formal_governance(self) -> bool:
        """Verifica se há política formal de governança nos documentos."""
        if not self.uploads_dir.exists():
            return False

        for fpath in self.uploads_dir.glob("*"):
            if fpath.suffix.lower() not in {".pdf", ".docx", ".txt", ".doc"}:
                continue
            text = self._safe_extract_text(fpath).lower()
            if any(kw in text for kw in _GOVERNANCE_KEYWORDS):
                log.debug("Governança formal detectada em: %s", fpath.name)
                return True
        return False

    def _count_similar_events(self) -> int:
        """
        Conta eventos de natureza cibernética no histórico persistido (SQLite).

        Este valor alimenta λ da distribuição Poisson no Monte Carlo (variável H).
        A contagem inclui todos os tipos de evento classificados como cyber-related
        pela lista _CYBER_EVENT_TYPES.

        Returns
        -------
        int
            Número de eventos similares no banco de dados.
        """
        try:
            history = get_event_history()  # lista de dicts com chave "evento"
            count = sum(
                1
                for record in history
                if record.get("evento", {}).get("tipo", "").lower()
                in _CYBER_EVENT_TYPES
                or record.get("evento", {}).get("type", "").lower()
                in _CYBER_EVENT_TYPES
            )
            log.debug("Eventos similares no histórico: %d", count)
            return count
        except Exception as exc:
            log.warning("Erro ao contar eventos históricos: %s", exc)
            return 0

    # -----------------------------------------------------------------------
    # Helpers de extração de texto
    # -----------------------------------------------------------------------

    def _safe_extract_text(self, fpath: Path) -> str:
        """Extrai texto de arquivo com tratamento de erro."""
        try:
            return extract_text(str(fpath))
        except Exception as exc:
            log.debug("Erro ao extrair texto de %s: %s", fpath.name, exc)
            return ""

    @staticmethod
    def _parse_maturity_from_text(text: str) -> float:
        """Procura nível de maturidade explícito no texto (padrões PT/EN)."""
        patterns = [
            r"n[íi]vel\s+de\s+maturidade[\s:]+(\d)",
            r"n[íi]vel\s+(\d)",
            r"maturity\s+level[\s:]+(\d)",
            r"level\s+(\d)",
            r"capability\s+level[\s:]+(\d)",
        ]
        text_lower = text.lower()
        for pattern in patterns:
            m = re.search(pattern, text_lower)
            if m:
                level = int(m.group(1))
                if 1 <= level <= 5:
                    return float(level)
        return 0.0


# ---------------------------------------------------------------------------
# Helper de módulo
# ---------------------------------------------------------------------------

async def collect_context() -> OrganizationalContextC2M:
    """Atalho para coletar contexto com instância fresh do Supervisor 3."""
    return await SupervisorContinuityRecovery().collect_organizational_context()
