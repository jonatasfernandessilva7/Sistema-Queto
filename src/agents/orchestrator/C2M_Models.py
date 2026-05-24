"""
C2M - Cyber Crisis Management Models

Estruturas de dados para o modelo C2M
Conforme ISO 22361, 31000, 22324, 22325
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from textblob import TextBlob


@dataclass
class SentimentAnalysisC2M:
    """Análise de sentimento TextBlob (-0.5 a +0.5)"""
    polarity: float
    subjectivity: float
    raw_text: str
    interpretation: str
    
    @classmethod
    def analyze(cls, text: str) -> 'SentimentAnalysisC2M':
        """Utiliza TextBlob para análise de sentimento"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
        except Exception as e:
            print(f"Erro ao analisar sentimento: {e}")
            polarity = 0.0
            subjectivity = 0.0
        
        if polarity > 0.1:
            interpretation = "Positivo"
        elif polarity < -0.1:
            interpretation = "Negativo"
        else:
            interpretation = "Neutro"
        
        return cls(
            polarity=polarity,
            subjectivity=subjectivity,
            raw_text=text[:200] if len(text) > 200 else text,
            interpretation=interpretation
        )
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RiskAgentC2M:
    """Agente de Risco - ISO 31000"""
    name: str
    category: str  # internal, external, human, technological, regulatory, reputational
    severity: float  # 0 a 1
    impact_chain: List[str]  # Impactos em cascata
    mitigation: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CrisisScenarioC2M:
    """Cenário de Escalação de Crise"""
    name: str
    probability: float  # 0 a 1
    affected_agents: List[str]
    impact_description: str
    impact_level: float  # 0 a 1
    escalation_path: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class OrganizationalContextC2M:
    """Contexto Organizacional para Análise"""
    maturity_level: float  # 1 a 5 (ISO 22325)
    has_risk_plan: bool
    has_crisis_plan: bool
    has_continuity_plan: bool
    has_recovery_plan: bool
    historical_similar_events: int
    formal_governance: bool
    
    def get_governance_score(self) -> float:
        """Calcula score de governança (0 a 1)"""
        plans = sum([
            self.has_risk_plan,
            self.has_crisis_plan,
            self.has_continuity_plan,
            self.has_recovery_plan
        ]) / 4
        return plans
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ISO 22324 - Codificação de Cores e Prioridades
ISO_22324_COLORS = {
    "Crítico": "#FF0000",
    "Alta": "#FFA500",
    "Moderada": "#FFFF00",
    "Baixa": "#00FF00",
    "Desconhecida": "#808080"
}

ISO_22324_LEVELS = {
    "Crítico": 5,
    "Alta": 4,
    "Moderada": 3,
    "Baixa": 2,
    "Desconhecida": 1
}

# Configuração de Monte Carlo
MONTE_CARLO_SIMULATIONS = 50000

# Limiar de crise
CRISIS_THRESHOLD = 0.4
CRISIS_PROBABILITY_THRESHOLD = 0.5  # 50%
