"""
Orquestrador Completo C2M
Executa os 4 estágios do modelo C2M

Estágio 1: Extração (chama 3 supervisores)
Estágio 2: Decision Tree
Estágio 3: Monte Carlo
Estágio 4: Geração de Relatório
"""

import json
import logging
from typing import Dict, Optional

from src.core.models import EventModel
from src.core.config.settings import Settings
from src.backend.utils.ConnectionWithLlamaApiGroqUtils import llama_api_call
from src.agents.orchestrator.C2M_Models import (
    SentimentAnalysisC2M,
    OrganizationalContextC2M,
    ISO_22324_COLORS,
    ISO_22324_LEVELS
)
from src.agents.orchestrator.SupervisorOrganizationalEnvironment import SupervisorOrganizationalEnvironment
from src.agents.orchestrator.SupervisorRiskManagement import SupervisorRiskManagement
from src.agents.orchestrator.SupervisorContinuityRecovery import SupervisorContinuityRecovery, collect_context
from src.agents.orchestrator.C2M_Analysis import DecisionTreeAnalyzer, MonteCarloProbabilityCalculator

log = logging.getLogger(__name__)


class C2MOrchestrator:
    """
    Orquestrador Central do Modelo C2M
    
    Executa fluxo completo:
    Evento → Supervisores → Decision Tree → Monte Carlo → Relatório
    """
    
    def __init__(self):
        self.supervisor_org = SupervisorOrganizationalEnvironment()
        self.supervisor_risk = SupervisorRiskManagement()
        self.supervisor_cont = SupervisorContinuityRecovery()
    
    async def process_event(
        self,
        event: EventModel,
        use_llm_enhancement: bool = True
    ) -> Dict:
        """
        Processa evento completamente conforme modelo C2M
        
        Retorna Dict com:
        {
            "status": "success" | "error",
            "probability_pct": float,
            "priority": str,
            "sentiment": SentimentAnalysisC2M,
            "risk_agents": List[RiskAgentC2M],
            "organizational_context": OrganizationalContextC2M,
            "crisis_scenarios": List[CrisisScenarioC2M],
            "decision_tree": {
                "is_potential_crisis": bool,
                "confidence_score": float,
                "reasoning": str
            },
            "analysis_summary": str
        }
        """
        
        try:
            log.info("═" * 80)
            log.info("INICIANDO PROCESSAMENTO C2M")
            log.info("═" * 80)
            
            # ════════════════════════════════════════════════════════════════════════
            # ESTÁGIO 1: EXTRAÇÃO (Supervisores)
            # ════════════════════════════════════════════════════════════════════════
            
            log.info("\n📊 ESTÁGIO 1: EXTRAÇÃO")
            log.info("─" * 80)
            
            # Supervisor 1: Sentimento
            log.info("Supervisor 1: Analisando ambiente organizacional...")
            sentiment = await self.supervisor_org.analyze_event(event)
            crisis_signals = self.supervisor_org.detect_crisis_signals(
                sentiment, 
                event.type, 
                event.details
            )
            log.info(f"  → Sentimento: {sentiment.interpretation} ({sentiment.polarity:.2f})")
            log.info(f"  → Sinais de crise: {len(crisis_signals['keywords_found'])} keywords encontradas")
            
            # Supervisor 3: Contexto (precisa rodar primeiro)
            log.info("Supervisor 3: Coletando contexto organizacional...")
            context = await collect_context()
            log.info(f"  → Maturidade: {context.maturity_level}/5.0")
            log.info(f"  → Planos: Crisis={context.has_crisis_plan}, Continuidade={context.has_continuity_plan}")
            
            # Supervisor 2: Riscos (usa context)
            log.info("Supervisor 2: Identificando agentes de risco...")
            risk_agents = await self.supervisor_risk.extract_risk_agents(event, context)
            log.info(f"  → {len(risk_agents)} agentes de risco identificados")
            
            # ════════════════════════════════════════════════════════════════════════
            # ESTÁGIO 2: ÁRVORE DE DECISÃO
            # ════════════════════════════════════════════════════════════════════════
            
            log.info("\n🌳 ESTÁGIO 2: DECISION TREE")
            log.info("─" * 80)
            
            is_potential_crisis, decision_score, decision_reasoning = DecisionTreeAnalyzer.evaluate(
                sentiment,
                event.type,
                context
            )
            
            decision_result = {
                "is_potential_crisis": is_potential_crisis,
                "confidence_score": decision_score,
                "reasoning": decision_reasoning
            }
            
            if not is_potential_crisis:
                log.info(f"⚠️ Score {decision_score:.2f} < Threshold {0.4}")
                log.info("Evento não apresenta potencial de crise, retornando análise simplificada")
                
                return {
                    "status": "success",
                    "probability_pct": 0.0,
                    "priority": "Desconhecida",
                    "sentiment": sentiment.to_dict(),
                    "risk_agents": [a.to_dict() for a in risk_agents],
                    "organizational_context": context.to_dict(),
                    "crisis_scenarios": [],
                    "decision_tree": decision_result,
                    "analysis_summary": f"Evento analisado. Score de crise: {decision_score:.2f}/1.00. Sem potencial imediato de crise.",
                    "low_risk_assessment": True
                }
            
            # ════════════════════════════════════════════════════════════════════════
            # ESTÁGIO 3: MONTE CARLO
            # ════════════════════════════════════════════════════════════════════════
            
            log.info("\n🎲 ESTÁGIO 3: MONTE CARLO (50.000 SIMULAÇÕES)")
            log.info("─" * 80)
            
            probability_pct, crisis_scenarios = MonteCarloProbabilityCalculator.run_simulation(
                risk_agents,
                context,
                sentiment.polarity
            )
            
            priority = MonteCarloProbabilityCalculator.classify_priority(probability_pct)
            
            # ════════════════════════════════════════════════════════════════════════
            # ESTÁGIO 4: ANÁLISE COMPLEMENTAR COM LLM
            # ════════════════════════════════════════════════════════════════════════
            
            log.info("\n🤖 ESTÁGIO 4: ANÁLISE COMPLEMENTAR")
            log.info("─" * 80)
            
            analysis_summary = await self._generate_analysis_summary(
                event,
                sentiment,
                risk_agents,
                crisis_scenarios,
                probability_pct,
                priority,
                context,
                use_llm_enhancement
            )
            
            # ════════════════════════════════════════════════════════════════════════
            # RESULTADO FINAL
            # ════════════════════════════════════════════════════════════════════════
            
            log.info("\n✅ PROCESSAMENTO COMPLETADO")
            log.info("═" * 80)
            
            return {
                "status": "success",
                "probability_pct": probability_pct,
                "priority": priority,
                "sentiment": sentiment.to_dict(),
                "risk_agents": [a.to_dict() for a in risk_agents],
                "organizational_context": context.to_dict(),
                "crisis_scenarios": [s.to_dict() for s in crisis_scenarios],
                "decision_tree": decision_result,
                "analysis_summary": analysis_summary,
                "crisis_signals": crisis_signals,
                "low_risk_assessment": False
            }
        
        except Exception as e:
            log.error(f"Erro ao processar evento C2M: {e}", exc_info=True)
            
            return {
                "status": "error",
                "error_message": str(e),
                "probability_pct": 0.0,
                "priority": "Desconhecida"
            }
    
    async def _generate_analysis_summary(
        self,
        event: EventModel,
        sentiment: SentimentAnalysisC2M,
        risk_agents: list,
        crisis_scenarios: list,
        probability_pct: float,
        priority: str,
        context: OrganizationalContextC2M,
        use_llm: bool = True
    ) -> str:
        """Gera sumário de análise, opcionalmente com LLM"""
        
        # Construir sumário estruturado
        summary = f"""
ANÁLISE C2M - RESUMO EXECUTIVO
{'=' * 80}

EVENTO: {event.type}
ORIGEM: {event.origin}
DATA/HORA: {event.details.get('timestamp', 'Não informado')}

PROBABILIDADE DE CRISE: {probability_pct:.1f}%
PRIORIDADE (ISO 22324): {priority}
COR DE ALERTA: {ISO_22324_COLORS.get(priority, '#808080')}

ANÁLISE DE SENTIMENTO:
  • Polarity: {sentiment.polarity:.2f}
  • Interpretation: {sentiment.interpretation}
  • Subjectivity: {sentiment.subjectivity:.2f}

AGENTES DE RISCO IDENTIFICADOS: {len(risk_agents)}
"""
        
        for i, agent in enumerate(risk_agents[:5], 1):
            summary += f"\n  {i}. {agent.name} ({agent.category})"
            summary += f"\n     Severidade: {agent.severity:.1%}"
            summary += f"\n     Mitigação: {agent.mitigation}"
        
        if len(risk_agents) > 5:
            summary += f"\n  ... e mais {len(risk_agents) - 5} agentes."
        
        summary += f"""

CONTEXTO ORGANIZACIONAL:
  • Maturidade: {context.maturity_level}/5.0 (ISO 22325)
  • Plano de Riscos: {'✓' if context.has_risk_plan else '✗'}
  • Plano de Crise: {'✓' if context.has_crisis_plan else '✗'}
  • Plano de Continuidade: {'✓' if context.has_continuity_plan else '✗'}
  • Plano de Recuperação: {'✓' if context.has_recovery_plan else '✗'}
  • Governança Formal: {'✓' if context.formal_governance else '✗'}

CENÁRIOS DE ESCALAÇÃO: {len(crisis_scenarios)}
"""
        
        for i, scenario in enumerate(crisis_scenarios[:3], 1):
            summary += f"\n  {i}. {scenario['name']}"
            summary += f"\n     Agentes Afetados: {', '.join(scenario['affected_agents'])}"
        
        summary += f"\n\nCONFORMIDADE: ISO 22361, 31000, 22324, 22325"
        
        # Se LLM disponível, enriquecer
        if use_llm:
            try:
                llm_prompt = f"""
Baseado na seguinte análise C2M, gere um sumário executivo profissional em português:

{summary}

Adicione:
1. Interpretação executiva do que há de crítico
2. Recomendações de ação imediata
3. Próximos passos importantes

Mantenha concisão e tom profissional.
"""
                enriched = await llama_api_call(llm_prompt)
                if enriched:
                    summary = enriched
            except Exception as e:
                log.debug(f"LLM indisponível, usando sumário estruturado: {e}")
        
        return summary
