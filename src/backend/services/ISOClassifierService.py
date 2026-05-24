"""
ISO Classifier Service - C2M
Implementa classificação de severidade conforme ISO 22324

ISO 22324:2018 - Security and resilience — Emergency management 
                  Guidelines for colour-coded alerts

Classifica crises em níveis baseado em probabilidade:
- VERDE (Green): Monitorar (P < 0.20)
- AMARELO (Yellow): Preparar (0.20 ≤ P < 0.40)
- LARANJA (Orange): Ativar comitê (0.40 ≤ P < 0.70)
- VERMELHO (Red): Crise declarada (P ≥ 0.70)
"""

import logging
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

log = logging.getLogger(__name__)


class CrisisLevel(Enum):
    """Níveis de crise conforme ISO 22324"""
    GREEN = "VERDE"
    YELLOW = "AMARELO"
    ORANGE = "LARANJA"
    RED = "VERMELHO"
    UNKNOWN = "DESCONHECIDO"


class CrisisColor(Enum):
    """Cores hexadecimais ISO 22324"""
    GREEN = "#00AA00"
    YELLOW = "#FFFF00"
    ORANGE = "#FF8800"
    RED = "#FF0000"
    UNKNOWN = "#808080"


@dataclass
class CrisisClassification:
    """Resultado da classificação de crise"""
    probability: float  # 0.0 a 1.0 (ou 0-100%)
    level: CrisisLevel
    color: str  # Código hexadecimal
    action_required: str
    description: str
    confidence_score: float  # 0.0 a 1.0
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            "probability": round(self.probability, 4),
            "level": self.level.value,
            "color": self.color,
            "action_required": self.action_required,
            "description": self.description,
            "confidence_score": round(self.confidence_score, 4),
            "timestamp": self.timestamp
        }


@dataclass
class DetailedCrisisReport:
    """Relatório detalhado de crise com recomendações"""
    classification: CrisisClassification
    contributing_factors: List[str]  # Fatores que contribuíram
    recommended_actions: List[str]   # Ações recomendadas
    risk_score: float                # Score agregado de risco
    maturity_impact: str             # Impacto da maturidade
    conformity_impact: str           # Impacto da conformidade
    sentiment_impact: str            # Impacto do sentimento
    next_steps: List[str]            # Próximos passos


class ISOClassifier:
    """
    Classificador de crises conforme ISO 22324
    
    Mapeia probabilidades a níveis de crise e ações associadas
    """
    
    # Thresholds ISO 22324
    THRESHOLDS = {
        0.70: (CrisisLevel.RED, CrisisColor.RED, "Crise declarada"),
        0.40: (CrisisLevel.ORANGE, CrisisColor.ORANGE, "Ativar comitê de crise"),
        0.20: (CrisisLevel.YELLOW, CrisisColor.YELLOW, "Preparar recursos"),
        0.00: (CrisisLevel.GREEN, CrisisColor.GREEN, "Monitorar situação"),
    }
    
    # Ações recomendadas por nível
    ACTIONS_BY_LEVEL = {
        CrisisLevel.GREEN: [
            "Manter monitoramento contínuo",
            "Realizar check-ins periódicos",
            "Documentar eventos para histórico",
            "Validar planos de resposta"
        ],
        CrisisLevel.YELLOW: [
            "Alertar equipe de crise",
            "Ativar sistema de notificação",
            "Revisar e validar planos",
            "Aumentar frequência de monitoramento",
            "Preparar recursos de resposta"
        ],
        CrisisLevel.ORANGE: [
            "Convocar comitê de crise",
            "Ativar plano de continuidade",
            "Comunicar ao executivo",
            "Mobilizar equipes especializadas",
            "Iniciar comunicação de crise",
            "Estabelecer salas de guerra"
        ],
        CrisisLevel.RED: [
            "Declarar crise formalmente",
            "Ativar todos os protocolos de crise",
            "Comunicação imediata com stakeholders",
            "Estabelecer comando e controle",
            "Ativar planos de recuperação",
            "Notificar autoridades regulatórias",
            "Iniciar gestão de mídia"
        ],
        CrisisLevel.UNKNOWN: [
            "Investigação adicional necessária",
            "Coletar mais dados",
            "Validar análise"
        ]
    }
    
    @staticmethod
    def classify(
        probability: float,
        confidence_score: float = 1.0
    ) -> CrisisClassification:
        """
        Classifica uma probabilidade em nível de crise
        
        Args:
            probability: Valor entre 0.0 e 1.0 (ou 0-100 se > 1)
            confidence_score: Confiança na análise [0, 1]
        
        Returns:
            CrisisClassification com nível e ações
        """
        # Normalizar se necessário
        if probability > 1.0:
            probability = probability / 100.0
        
        probability = float(max(0.0, min(1.0, probability)))
        confidence_score = float(max(0.0, min(1.0, confidence_score)))
        
        # Determinar nível
        level = CrisisLevel.UNKNOWN
        color = CrisisColor.UNKNOWN.value
        action = "Investigação necessária"
        
        for threshold, (lvl, clr, act) in ISOClassifier.THRESHOLDS.items():
            if probability >= threshold:
                level = lvl
                color = clr.value
                action = act
                break
        
        # Criar classificação
        timestamp = datetime.now().isoformat()
        description = ISOClassifier._generate_description(
            probability, level, confidence_score
        )
        
        classification = CrisisClassification(
            probability=probability,
            level=level,
            color=color,
            action_required=action,
            description=description,
            confidence_score=confidence_score,
            timestamp=timestamp
        )
        
        log.info(f"""
        ════════════════════════════════════════════════════════════════════════
        ISO 22324 CLASSIFICAÇÃO
        ════════════════════════════════════════════════════════════════════════
        Probabilidade: {probability:.2%}
        Nível: {level.value}
        Cor: {color}
        Confiança: {confidence_score:.2%}
        Ação: {action}
        ════════════════════════════════════════════════════════════════════════
        """)
        
        return classification
    
    @staticmethod
    def classify_detailed(
        probability: float,
        confidence_score: float = 1.0,
        sentiment_polarity: float = 0.0,
        maturity_level: float = 3.0,
        conformity_factor: float = 0.5,
        contributing_factors: List[str] = None
    ) -> DetailedCrisisReport:
        """
        Classificação detalhada com análise de fatores
        
        Args:
            probability: Probabilidade de crise [0, 1]
            confidence_score: Confiança na análise [0, 1]
            sentiment_polarity: Polaridade de sentimento [-0.5, 0.5]
            maturity_level: Nível de maturidade [1, 5]
            conformity_factor: Fator de conformidade [0, 1]
            contributing_factors: Lista de fatores contribuintes
        
        Returns:
            DetailedCrisisReport com análise completa
        """
        # Classificação base
        classification = ISOClassifier.classify(probability, confidence_score)
        
        # Fatores contribuintes
        if contributing_factors is None:
            contributing_factors = []
        
        # Análise de impactos
        sentiment_impact = ISOClassifier._analyze_sentiment_impact(sentiment_polarity)
        maturity_impact = ISOClassifier._analyze_maturity_impact(maturity_level)
        conformity_impact = ISOClassifier._analyze_conformity_impact(conformity_factor)
        
        # Ações recomendadas
        recommended_actions = ISOClassifier.ACTIONS_BY_LEVEL.get(
            classification.level, ISOClassifier.ACTIONS_BY_LEVEL[CrisisLevel.UNKNOWN]
        )
        
        # Score agregado de risco
        risk_score = ISOClassifier._calculate_risk_score(
            probability, sentiment_polarity, maturity_level, conformity_factor
        )
        
        # Próximos passos
        next_steps = ISOClassifier._define_next_steps(classification.level, risk_score)
        
        return DetailedCrisisReport(
            classification=classification,
            contributing_factors=contributing_factors,
            recommended_actions=recommended_actions,
            risk_score=risk_score,
            maturity_impact=maturity_impact,
            conformity_impact=conformity_impact,
            sentiment_impact=sentiment_impact,
            next_steps=next_steps
        )
    
    @staticmethod
    def _generate_description(
        probability: float,
        level: CrisisLevel,
        confidence: float
    ) -> str:
        """Gera descrição legível da classificação"""
        level_descriptions = {
            CrisisLevel.GREEN: "Situação sob controle. Continue monitorando.",
            CrisisLevel.YELLOW: "Risco detectado. Prepare equipes e recursos.",
            CrisisLevel.ORANGE: "Risco iminente. Ative o plano de crise.",
            CrisisLevel.RED: "CRISE DECLARADA. Execute protocolo de emergência completo.",
            CrisisLevel.UNKNOWN: "Classificação indeterminada. Necessária investigação."
        }
        
        desc = level_descriptions.get(level, "")
        return f"{desc} (Confiança: {confidence:.0%})"
    
    @staticmethod
    def _analyze_sentiment_impact(polarity: float) -> str:
        """Analisa impacto do sentimento"""
        if polarity < -0.3:
            return "Sentimento MUITO NEGATIVO - aumenta risco de crise"
        elif polarity < -0.1:
            return "Sentimento NEGATIVO - contribui ao risco"
        elif polarity < 0.1:
            return "Sentimento NEUTRO - impacto mínimo"
        else:
            return "Sentimento POSITIVO - reduz risco"
    
    @staticmethod
    def _analyze_maturity_impact(level: float) -> str:
        """Analisa impacto da maturidade"""
        if level < 2:
            return "Maturidade MUITO BAIXA - aumenta significativamente o risco"
        elif level < 3:
            return "Maturidade BAIXA - aumenta o risco"
        elif level < 4:
            return "Maturidade MODERADA - capacidade de resposta adequada"
        else:
            return "Maturidade ALTA - capacidade robusta de resposta"
    
    @staticmethod
    def _analyze_conformity_impact(factor: float) -> str:
        """Analisa impacto da conformidade"""
        if factor > 0.8:
            return "Conformidade CRÍTICA - grande divergência das políticas"
        elif factor > 0.5:
            return "Conformidade BAIXA - divergência significativa"
        elif factor > 0.3:
            return "Conformidade MODERADA - algumas discrepâncias"
        else:
            return "Conformidade ALTA - alinhamento com políticas"
    
    @staticmethod
    def _calculate_risk_score(
        probability: float,
        sentiment: float,
        maturity: float,
        conformity: float
    ) -> float:
        """
        Calcula score agregado de risco (0 a 1)
        
        Ponderação:
        - Probabilidade: 40%
        - Conformidade: 30%
        - Sentimento: 20%
        - Maturidade (inversa): 10%
        """
        sentiment_factor = max(0, abs(sentiment)) / 0.5  # 0-1
        maturity_factor = 1.0 - (maturity / 5.0)  # Inversa
        
        risk = (
            probability * 0.40 +
            conformity * 0.30 +
            sentiment_factor * 0.20 +
            maturity_factor * 0.10
        )
        
        return float(max(0.0, min(1.0, risk)))
    
    @staticmethod
    def _define_next_steps(level: CrisisLevel, risk_score: float) -> List[str]:
        """Define próximos passos recomendados"""
        steps = []
        
        if level == CrisisLevel.GREEN:
            steps = [
                "Revisar métricas em 24 horas",
                "Manter documentação atualizada",
                "Validar efetividade dos controles"
            ]
        elif level == CrisisLevel.YELLOW:
            steps = [
                "Briefing da equipe em 2 horas",
                "Reunião de planejamento em 4 horas",
                "Estar pronto para escalar em 8 horas"
            ]
        elif level == CrisisLevel.ORANGE:
            steps = [
                "Convocar comitê IMEDIATAMENTE",
                "Ativar centro de comando em 1 hora",
                "Comunicado interno em 2 horas",
                "Avaliação de impacto em 4 horas"
            ]
        elif level == CrisisLevel.RED:
            steps = [
                "ATIVAÇÃO IMEDIATA DE TODOS OS PROTOCOLOS",
                "Comando executivo em 15 minutos",
                "Comunicação externa em 1 hora",
                "Escalação para autoridades em 2 horas"
            ]
        
        return steps
    
    @staticmethod
    def get_thresholds() -> Dict[str, Tuple[str, str, float]]:
        """Retorna todos os thresholds ISO 22324"""
        return {
            "RED": ("VERMELHO", "#FF0000", 0.70),
            "ORANGE": ("LARANJA", "#FF8800", 0.40),
            "YELLOW": ("AMARELO", "#FFFF00", 0.20),
            "GREEN": ("VERDE", "#00AA00", 0.00),
        }


def classify_crisis(
    probability: float,
    confidence: float = 1.0
) -> CrisisClassification:
    """Helper function para classificar crise"""
    return ISOClassifier.classify(probability, confidence)


def classify_crisis_detailed(
    probability: float,
    confidence: float = 1.0,
    **kwargs
) -> DetailedCrisisReport:
    """Helper function para classificação detalhada"""
    return ISOClassifier.classify_detailed(probability, confidence, **kwargs)
