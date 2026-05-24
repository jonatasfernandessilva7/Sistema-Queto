"""
Estágio 2 (Decision Tree) + Estágio 3 (Monte Carlo)

Implementa o modelo probabilístico conforme especificado no artigo:

  P_crisis = w1*S_neg + w2*(1-M_norm) + w3*(1-P) + w4*H_norm + w5*C

Distribuições estocásticas por variável (seção 4.5.1):
  S  ~ Triangular(-0.5, S_obs, 0)   — apenas componente negativa contribui
  M  ~ Normal(μ_M, 15), clipped [0, 100], normalizado para [0, 1]
  P  ~ Bernoulli(p), p=0.8 se plano existe, p=0.3 se não existe
  H  ~ Poisson(λ), λ = freq. histórica de incidentes, norm. min(1, H/10)
  C  = fator de conformidade semântica (fixo por run, vindo do VectorSearch)

Pesos calibrados por especialistas (seção 4.5.2):
  w = [0.34, 0.255, 0.17, 0.085, 0.15]

ISO 22324 thresholds (seção 4.6):
  [0.00, 0.20) → GREEN   / Monitor
  [0.20, 0.40) → YELLOW  / Prepare
  [0.40, 0.70) → ORANGE  / Activate crisis committee
  [0.70, 1.00] → RED     / Declare crisis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Dict

import numpy as np

from src.agents.orchestrator.C2M_Models import (
    SentimentAnalysisC2M,
    RiskAgentC2M,
    CrisisScenarioC2M,
    OrganizationalContextC2M,
    CRISIS_THRESHOLD,
    MONTE_CARLO_SIMULATIONS,
)
from src.AiServices.services.WeightManager import get_weight_manager

log = logging.getLogger(__name__)

# Monte Carlo weight vector — expert-calibrated (seção 4.5.2 do artigo)

_MC_WEIGHTS = np.array([0.34, 0.255, 0.17, 0.085, 0.15])

# ISO 22324 thresholds (seção 4.6)  — único mapeamento no sistema inteiro
_ISO_THRESHOLDS: List[Tuple[float, str, str, str]] = [
    (0.70, "VERMELHO", "#FF0000", "Declarar crise"),
    (0.40, "LARANJA",  "#FF8800", "Ativar comitê de crise"),
    (0.20, "AMARELO",  "#FFFF00", "Preparar recursos"),
    (0.00, "VERDE",    "#00AA00", "Monitorar situação"),
]

@dataclass
class MonteCarloResult:
    """Saída completa do motor Monte Carlo (seção 4.5.3 / 4.5.4)."""

    # Probabilidade média P̄ ∈ [0, 1]
    mean_probability: float

    # Desvio padrão
    std_deviation: float

    # Intervalo de confiança 95% empírico
    ci_95_lower: float
    ci_95_upper: float

    # Percentis p10…p90
    percentiles: Dict[str, float]

    # Correlações de Pearson: variável → r (seção 4.5.4)
    pearson_correlations: Dict[str, float]

    # ISO 22324
    iso_level: str   # VERDE / AMARELO / LARANJA / VERMELHO
    iso_color: str   # hex
    iso_action: str

    # Prioridade em português (compatibilidade com relatório PDF)
    priority: str

    # Cenários de exemplo capturados (para sumário)
    crisis_scenarios: List[CrisisScenarioC2M] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "mean_probability": round(self.mean_probability, 4),
            "mean_probability_pct": round(self.mean_probability * 100, 2),
            "std_deviation": round(self.std_deviation, 4),
            "confidence_interval_95": {
                "lower": round(self.ci_95_lower, 4),
                "upper": round(self.ci_95_upper, 4),
            },
            "percentiles": {k: round(v, 4) for k, v in self.percentiles.items()},
            "pearson_correlations": {
                k: round(v, 4) if not np.isnan(v) else None
                for k, v in self.pearson_correlations.items()
            },
            "iso_22324": {
                "level": self.iso_level,
                "color": self.iso_color,
                "action": self.iso_action,
            },
            "priority": self.priority,
            "crisis_scenarios": [s.to_dict() for s in self.crisis_scenarios],
        }


# Helpers e classes de análise para os estágios 2 e 3 do pipeline C2M

def _iso_classify(mean_p: float) -> Tuple[str, str, str, str]:
    """Mapeia P̄ ∈ [0,1] para (level, color, action, priority_pt)."""
    priority_map = {
        "VERMELHO": "Crítico",
        "LARANJA": "Alta",
        "AMARELO": "Moderada",
        "VERDE": "Baixa",
    }
    for threshold, level, color, action in _ISO_THRESHOLDS:
        if mean_p >= threshold:
            return level, color, action, priority_map[level]
    return "VERDE", "#00AA00", "Monitorar situação", "Baixa"


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    """Coeficiente de Pearson com guard para variância zero."""
    if np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


# ESTÁGIO 2 — Decision Tree

class DecisionTreeAnalyzer:
    """
    Filtragem inicial antes do Monte Carlo.

    Score ∈ [0, 1] composto por quatro fatores (25% cada):
      1. Negatividade do sentimento
      2. Tipo de evento crítico (keywords)
      3. Falta de governança
      4. Baixa maturidade organizacional

    Se score > threshold → evento passa para Monte Carlo.
    Threshold lido do WeightManager para que o RLHF tenha efeito em runtime.
    """

    _CRITICAL_KEYWORDS = frozenset({
        "ataque", "attack", "intrusion", "intrusão",
        "falha", "failure", "indisponível", "unavailable",
        "indisponibilidade", "unavailability", "violação",
        "violation", "breach", "ransomware", "malware",
        "comprometimento", "compromise", "roubo", "theft",
        "vazamento", "leak",
    })

    @staticmethod
    def evaluate(
        sentiment: SentimentAnalysisC2M,
        event_type: str,
        context: OrganizationalContextC2M,
    ) -> Tuple[bool, float, str]:
        """
        Avalia se o evento deve acionar o Monte Carlo.

        Returns
        -------
        (is_potential_crisis, score, reasoning)
        """
        wm = get_weight_manager()

        score = 0.0
        factors: List[str] = []

        # Fator 1: sentimento negativo (muda conforme RLHF via WeightManager)
        w_sentiment = wm.get_weight("decision_tree_sentiment") or 0.25
        if sentiment.polarity < -0.1:
            intensity = abs(sentiment.polarity) / 0.5  # normaliza para [0, 1]
            f1 = intensity * w_sentiment
            score += f1
            factors.append(
                f"Sentimento {sentiment.interpretation} "
                f"(polarity={sentiment.polarity:.2f}, contribuição={f1:.3f})"
            )
        else:
            factors.append(f"Sentimento {sentiment.interpretation} ({sentiment.polarity:.2f})")

        # Fator 2: tipo de evento crítico
        w_type = wm.get_weight("decision_tree_type") or 0.25
        if any(kw in event_type.lower() for kw in DecisionTreeAnalyzer._CRITICAL_KEYWORDS):
            score += w_type
            factors.append(f"Tipo de evento crítico: '{event_type}' (contribuição={w_type:.3f})")
        else:
            factors.append(f"Tipo de evento: '{event_type}'")

        # Fator 3: falta de governança
        w_gov = wm.get_weight("decision_tree_governance") or 0.25
        gov_score = context.get_governance_score()
        if gov_score < 0.5:
            f3 = (1.0 - gov_score) * w_gov
            score += f3
            factors.append(
                f"Governança insuficiente (score={gov_score:.2f}, contribuição={f3:.3f})"
            )
        else:
            factors.append(f"Governança adequada (score={gov_score:.2f})")

        # Fator 4: baixa maturidade
        w_mat = wm.get_weight("decision_tree_maturity") or 0.25
        mat_norm = context.maturity_level / 5.0
        if mat_norm < 0.4:
            f4 = (1.0 - mat_norm) * w_mat
            score += f4
            factors.append(
                f"Maturidade baixa ({context.maturity_level}/5.0, contribuição={f4:.3f})"
            )
        else:
            factors.append(f"Maturidade adequada ({context.maturity_level}/5.0)")

        score = float(np.clip(score, 0.0, 1.0))
        threshold = wm.get_weight("crisis_threshold") or CRISIS_THRESHOLD
        is_crisis = score > threshold
        reasoning = "; ".join(factors)

        log.info(
            "Decision Tree → score=%.3f threshold=%.2f decisão=%s",
            score, threshold, "CRISE" if is_crisis else "SEM_CRISE",
        )
        return is_crisis, score, reasoning



# ESTÁGIO 3 — Monte Carlo

class MonteCarloProbabilityCalculator:
    """
    Motor de inferência probabilística via simulação Monte Carlo.

    Implementa exatamente a fórmula do artigo (seção 4.5):

        P_crisis_i = w1·S_neg + w2·(1−M_norm) + w3·(1−P) + w4·H_norm + w5·C

    Todas as variáveis são amostradas de suas distribuições especificadas.
    O seed NÃO é fixo — cada execução produz resultados estocásticos distintos,
    conforme o fundamento do método Monte Carlo.
    """

    @staticmethod
    def run_simulation(
        context: OrganizationalContextC2M,
        sentiment_polarity: float,
        conformity_factor: float,
        num_simulations: int = MONTE_CARLO_SIMULATIONS,
    ) -> MonteCarloResult:
        """
        Executa N simulações e retorna distribuição completa de P_crisis.

        Parameters
        ----------
        context : OrganizationalContextC2M
            Contexto organizacional coletado pelo Supervisor 3.
        sentiment_polarity : float
            Polaridade observada em [-0.5, 0.5].
        conformity_factor : float
            Fator de divergência de governança C ∈ [0, 1] do VectorSearchService.
        num_simulations : int
            Número de cenários Monte Carlo (padrão: 50 000).

        Returns
        -------
        MonteCarloResult
            Estatísticas completas + classificação ISO 22324.
        """
        N = num_simulations
        rng = np.random.default_rng()  # seed aleatório por execução

        log.info("Monte Carlo: iniciando %d simulações", N)

        # 1. Amostrar variáveis estocásticas 

        # S — Sentimento: Triangular(-0.5, S_obs, 0)
        # Somente componente negativa escalona risco: S_neg = max(0, -S)
        s_obs = float(np.clip(sentiment_polarity, -0.5, 0.0))
        S_raw = rng.triangular(left=-0.5, mode=s_obs, right=0.0, size=N)
        S_neg = np.maximum(0.0, -S_raw)  # S_neg ∈ [0, 0.5]

        # M — Maturidade: Normal(μ_M, 15), clipped [0, 100], normalizado
        # μ_M em escala [0,100] = maturity_level * 20  (onde maturity ∈ [1,5])
        mu_M = context.maturity_level * 20.0
        M_raw = np.clip(rng.normal(loc=mu_M, scale=15.0, size=N), 0.0, 100.0)
        M_norm = M_raw / 100.0  # ∈ [0, 1]

        # P — Plano de continuidade: Bernoulli(p)
        p_plan = 0.8 if context.has_continuity_plan else 0.3
        P_plan = rng.binomial(n=1, p=p_plan, size=N).astype(np.float64)

        # H — Histórico de incidentes: Poisson(λ), normalizado min(1, H/10)
        lam = max(0.0, float(context.historical_similar_events))
        H_raw = rng.poisson(lam=lam, size=N).astype(np.float64)
        H_norm = np.minimum(1.0, H_raw / 10.0)

        # C — Conformidade: valor fixo por run (do VectorSearchService)
        C = float(np.clip(conformity_factor, 0.0, 1.0))
        C_vec = np.full(N, C)

        # 2. Calcular P_crisis para cada cenário 
        w = _MC_WEIGHTS
        P_crisis = (
            w[0] * S_neg
            + w[1] * (1.0 - M_norm)
            + w[2] * (1.0 - P_plan)
            + w[3] * H_norm
            + w[4] * C_vec
        )
        P_crisis = np.clip(P_crisis, 0.0, 1.0)

        # 3. Agregação estatística (seção 4.5.3) 
        mean_p = float(np.mean(P_crisis))
        std_p  = float(np.std(P_crisis, ddof=1))
        ci_lo  = float(np.percentile(P_crisis, 2.5))
        ci_hi  = float(np.percentile(P_crisis, 97.5))
        pcts: Dict[str, float] = {
            f"p{k}": float(np.percentile(P_crisis, k))
            for k in (10, 25, 50, 75, 90)
        }

        # 4. Correlações de Pearson (seção 4.5.4) 
        factor_arrays = {
            "sentimento":    S_neg,
            "maturidade":    1.0 - M_norm,   # contribuição: menor maturidade → maior risco
            "continuidade":  1.0 - P_plan,
            "historico":     H_norm,
            "conformidade":  C_vec,
        }
        pearson: Dict[str, float] = {
            name: _pearson(vec, P_crisis)
            for name, vec in factor_arrays.items()
        }

        # 5. Classificação ISO 22324 (seção 4.6) 
        level, color, action, priority = _iso_classify(mean_p)

        # 6. Amostrar cenários representativos 
        crisis_mask = P_crisis > 0.5
        n_crisis = int(np.sum(crisis_mask))
        crisis_scenarios: List[CrisisScenarioC2M] = []
        if n_crisis > 0:
            sample_idx = np.where(crisis_mask)[0][:10]
            for i, idx in enumerate(sample_idx):
                crisis_scenarios.append(
                    CrisisScenarioC2M(
                        name=f"Cenário de Escalação #{i + 1}",
                        probability=float(P_crisis[idx]),
                        affected_agents=[],
                        impact_description=(
                            f"P_crisis={P_crisis[idx]:.3f} | "
                            f"S_neg={S_neg[idx]:.3f} | "
                            f"M_norm={M_norm[idx]:.3f} | "
                            f"P={P_plan[idx]:.0f} | "
                            f"H={H_norm[idx]:.3f} | "
                            f"C={C:.3f}"
                        ),
                        impact_level=float(P_crisis[idx]),
                        escalation_path=f"Simulação #{idx}",
                    )
                )

        result = MonteCarloResult(
            mean_probability=round(mean_p, 4),
            std_deviation=round(std_p, 4),
            ci_95_lower=round(ci_lo, 4),
            ci_95_upper=round(ci_hi, 4),
            percentiles=pcts,
            pearson_correlations=pearson,
            iso_level=level,
            iso_color=color,
            iso_action=action,
            priority=priority,
            crisis_scenarios=crisis_scenarios,
        )

        log.info(
            "Monte Carlo: P̄=%.4f σ=%.4f CI=[%.4f, %.4f] ISO=%s",
            mean_p, std_p, ci_lo, ci_hi, level,
        )
        log.info(
            "Pearson: %s",
            {k: f"{v:.3f}" for k, v in pearson.items() if not np.isnan(v)},
        )

        return result
