"""
Estágio 2: Decision Tree Analyzer
Estágio 3: Monte Carlo Probability Calculator

Lógica central de análise probabilística do modelo C2M
"""

import logging
import numpy as np
from typing import Tuple, List

from src.agents.orchestrator.C2M_Models import (
    SentimentAnalysisC2M,
    RiskAgentC2M,
    CrisisScenarioC2M,
    OrganizationalContextC2M,
    CRISIS_THRESHOLD,
    MONTE_CARLO_SIMULATIONS
)

log = logging.getLogger(__name__)


class DecisionTreeAnalyzer:
    """
    Estágio 2: Árvore de Decisão
    
    Determina se o evento deve passar para análise probabilística (Monte Carlo)
    
    Fatores avaliados:
    1. Sentimento negativo?
    2. Tipo de evento crítico?
    3. Governança adequada?
    4. Maturidade baixa?
    """
    
    @staticmethod
    def evaluate(
        sentiment: SentimentAnalysisC2M,
        event_type: str,
        context: OrganizationalContextC2M
    ) -> Tuple[bool, float, str]:
        """
        Avalia se evento representa potencial crise
        
        Args:
            sentiment: Análise de sentimento do evento
            event_type: Tipo do evento
            context: Contexto organizacional
        
        Returns:
            (is_potential_crisis: bool, confidence_score: float, reasoning: str)
        """
        
        score = 0.0
        factors = []
        
        # ════════════════════════════════════════════════════════════════════════
        # FATOR 1: SENTIMENTO NEGATIVO (25%)
        # ════════════════════════════════════════════════════════════════════════
        
        if sentiment.polarity < -0.1:
            sentimento_intensity = abs(sentiment.polarity) / 0.5  # Normalizar para max 0.5
            factor_1 = sentimento_intensity * 0.25
            score += factor_1
            factors.append(f"Sentimento negativo: {sentiment.interpretation} (polarity={sentiment.polarity:.2f})")
            log.debug(f"Fator 1 (Sentimento): +{factor_1:.2f}")
        else:
            factors.append(f"Sentimento {sentiment.interpretation} (polarity={sentiment.polarity:.2f})")
        
        # ════════════════════════════════════════════════════════════════════════
        # FATOR 2: TIPO DE EVENTO CRÍTICO (25%)
        # ════════════════════════════════════════════════════════════════════════
        
        critical_keywords = [
            "ataque", "attack", "intrusion", "intrusão", "falha", "failure",
            "indisponível", "unavailable", "indisponibilidade", "unavailability",
            "violação", "violation", "breach", "ransomware", "malware",
            "comprometimento", "compromise", "roubo", "theft", "vazamento", "leak"
        ]
        
        event_type_lower = event_type.lower()
        if any(keyword in event_type_lower for keyword in critical_keywords):
            score += 0.25
            factors.append(f"Tipo de evento crítico identificado: {event_type}")
            log.debug(f"Fator 2 (Tipo): +0.25")
        else:
            factors.append(f"Tipo de evento: {event_type}")
        
        # ════════════════════════════════════════════════════════════════════════
        # FATOR 3: FALTA DE GOVERNANÇA (25%)
        # ════════════════════════════════════════════════════════════════════════
        
        governance_score = context.get_governance_score()
        if governance_score < 0.5:
            factor_3 = (1 - governance_score) * 0.25
            score += factor_3
            factors.append(f"Governança inadequada (score={governance_score:.2f})")
            log.debug(f"Fator 3 (Governança): +{factor_3:.2f}")
        else:
            factors.append(f"Governança adequada (score={governance_score:.2f})")
        
        # ════════════════════════════════════════════════════════════════════════
        # FATOR 4: BAIXA MATURIDADE ORGANIZACIONAL (25%)
        # ════════════════════════════════════════════════════════════════════════
        
        maturity_normalized = context.maturity_level / 5.0
        if maturity_normalized < 0.4:
            factor_4 = (1 - maturity_normalized) * 0.25
            score += factor_4
            factors.append(f"Maturidade baixa ({context.maturity_level}/5.0)")
            log.debug(f"Fator 4 (Maturidade): +{factor_4:.2f}")
        else:
            factors.append(f"Maturidade adequada ({context.maturity_level}/5.0)")
        
        # ════════════════════════════════════════════════════════════════════════
        # DECISÃO FINAL
        # ════════════════════════════════════════════════════════════════════════
        
        score = min(1.0, max(0.0, score))
        is_crisis = score > CRISIS_THRESHOLD
        reasoning = "; ".join(factors)
        
        log.info(f"""
        ════════════════════════════════════════════════════════════════════════
        DECISION TREE RESULTADO:
        ════════════════════════════════════════════════════════════════════════
        Score Final: {score:.2f}/1.00
        Threshold: {CRISIS_THRESHOLD}
        Decisão: {'POTENCIAL CRISE ⚠️' if is_crisis else 'SEM POTENCIAL DE CRISE ✓'}
        
        Fatores Avaliados:
        {'; '.join([f'• {f}' for f in factors])}
        ════════════════════════════════════════════════════════════════════════
        """)
        
        return is_crisis, score, reasoning


class MonteCarloProbabilityCalculator:
    """
    Estágio 3: Simulação Probabilística Monte Carlo
    
    Executa 50.000 simulações para calcular probabilidade de crise
    
    Lógica:
    - Para cada simulação, tenta ativar cada agente de risco probabilisticamente
    - Crise acontece se 2+ agentes são ativados
    - Conta quantas simulações resultaram em crise
    - Calcula porcentagem
    """
    
    @staticmethod
    def run_simulation(
        risk_agents: List[RiskAgentC2M],
        context: OrganizationalContextC2M,
        sentiment_polarity: float,
        num_simulations: int = MONTE_CARLO_SIMULATIONS
    ) -> Tuple[float, List[CrisisScenarioC2M]]:
        """
        Executa simulação de Monte Carlo
        
        Args:
            risk_agents: Lista de agentes de risco identificados
            context: Contexto organizacional
            sentiment_polarity: Polaridade de sentimento (-0.5 a +0.5)
            num_simulations: Número de iterações (padrão: 50.000)
        
        Returns:
            (probability_pct: float, crisis_scenarios: List[CrisisScenarioC2M])
        """
        
        if not risk_agents:
            log.warning("Nenhum agente de risco fornecido, returnando probabilidade 0%")
            return 0.0, []
        
        crisis_count = 0
        scenarios_buffer = []
        
        # Seed para reproducibilidade
        np.random.seed(42)
        
        log.info(f"Iniciando simulação Monte Carlo: {num_simulations:,} iterações")
        log.info(f"Agentes de risco: {len(risk_agents)}")
        log.info(f"Sentimento polarity: {sentiment_polarity:.2f}")
        log.info(f"Maturidade organizacional: {context.maturity_level}/5.0")
        
        # ════════════════════════════════════════════════════════════════════════
        # SIMULAÇÕES
        # ════════════════════════════════════════════════════════════════════════
        
        for sim_idx in range(num_simulations):
            activated_agents = []
            
            # Para cada agente, decidir se ativa probabilisticamente
            for agent in risk_agents:
                
                # Probabilidade base do agente
                base_prob = agent.severity
                
                # MODIFICADOR 1: Sentimento negativo aumenta ativação
                # Se polarity < 0 (negativo), aumentar probabilidade
                sentiment_multiplier = 0.0
                if sentiment_polarity < 0:
                    sentiment_factor = abs(sentiment_polarity) / 0.5  # Normalizar
                    sentiment_multiplier = sentiment_factor * 0.2  # Max +20%
                
                # MODIFICADOR 2: Baixa maturidade aumenta ativação
                # Se maturidade < 2, aumentar muito
                maturity_factor = (1 - context.maturity_level / 5.0) * 0.3  # Max +30%
                
                # MODIFICADOR 3: Falta de governança aumenta ativação
                governance_factor = (1 - context.get_governance_score()) * 0.1  # Max +10%
                
                # Probabilidade final
                activation_prob = base_prob + sentiment_multiplier + maturity_factor + governance_factor
                activation_prob = min(1.0, max(0.0, activation_prob))  # Clamp 0-1
                
                # Ativar agent?
                if np.random.random() < activation_prob:
                    activated_agents.append(agent)
            
            # ════════════════════════════════════════════════════════════════════════
            # DEFINIÇÃO DE CRISE: 2+ AGENTES ATIVADOS
            # ════════════════════════════════════════════════════════════════════════
            
            if len(activated_agents) >= 2:
                crisis_count += 1
                
                # Armazenar amostra de cenários (primeiras 10)
                if len(scenarios_buffer) < 10:
                    # Construir impact_chain da escalação
                    escalation_path = " → ".join([a.name for a in activated_agents])
                    
                    scenario = CrisisScenarioC2M(
                        name=f"Cenário de Escalação #{len(scenarios_buffer) + 1}",
                        probability=len(activated_agents) / len(risk_agents),
                        affected_agents=[a.name for a in activated_agents],
                        impact_description=f"{len(activated_agents)} agentes de risco ativados em cascata: {escalation_path}",
                        impact_level=np.mean([a.severity for a in activated_agents]),
                        escalation_path=escalation_path
                    )
                    scenarios_buffer.append(scenario)
        
        # ════════════════════════════════════════════════════════════════════════
        # CÁLCULO FINAL
        # ════════════════════════════════════════════════════════════════════════
        
        probability_pct = (crisis_count / num_simulations) * 100
        
        log.info(f"""
        ════════════════════════════════════════════════════════════════════════
        MONTE CARLO RESULTADO:
        ════════════════════════════════════════════════════════════════════════
        Simulações com 2+ agentes ativados: {crisis_count:,} / {num_simulations:,}
        Probabilidade de Crise: {probability_pct:.2f}%
        Cenários únicos capturados: {len(scenarios_buffer)}
        ════════════════════════════════════════════════════════════════════════
        """)
        
        return probability_pct, scenarios_buffer
    
    @staticmethod
    def classify_priority(probability_pct: float) -> str:
        """
        Classifica prioridade baseado em probabilidade
        
        Baseado em ISO 22324 (Color Coding)
        """
        
        if probability_pct > 70:
            return "Crítico"
        elif probability_pct > 50:
            return "Alta"
        elif probability_pct > 30:
            return "Moderada"
        elif probability_pct > 10:
            return "Baixa"
        else:
            return "Desconhecida"
