"""
Estágio 1: Extração  → 3 Supervisores (Org, Risk, Continuity)
Estágio 2: Decision Tree → filtragem inicial (DecisionTreeAnalyzer)
Estágio 3: Monte Carlo  → inferência probabilística (MonteCarloProbabilityCalculator)
Estágio 4: Sumário      → relatório estruturado ± enriquecimento LLM

Principais correções em relação à versão anterior:
  - VectorSearchService integrado ao pipeline: conformity_factor alimenta o Monte Carlo
  - Monte Carlo usa MonteCarloResult (não tupla ad-hoc)
  - ISOClassifierService usado para classificação final (não classify_priority local)
  - WeightManager consultado em runtime para threshold da Decision Tree
  - Resultado final inclui todos os campos estatísticos (IC 95%, percentis, Pearson)
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from src.agents.orchestrator.C2M_Analysis import (
    DecisionTreeAnalyzer,
    MonteCarloProbabilityCalculator,
    MonteCarloResult,
)
from src.agents.orchestrator.C2M_Models import (
    ISO_22324_COLORS,
    ISO_22324_LEVELS,
    OrganizationalContextC2M,
    SentimentAnalysisC2M,
)
from src.agents.orchestrator.SupervisorContinuityRecovery import (
    SupervisorContinuityRecovery,
    collect_context,
)
from src.agents.orchestrator.SupervisorOrganizationalEnvironment import (
    SupervisorOrganizationalEnvironment,
)
from src.agents.orchestrator.SupervisorRiskManagement import SupervisorRiskManagement
from src.backend.services.VectorSearchService import calculate_conformity
from src.core.utils.llama_api_utils import llama_api_call
from src.core.config.settings import Settings
from src.core.models import EventModel

log = logging.getLogger(__name__)

class C2MOrchestrator:
    """
    Orquestrador Central do Modelo C2M.

    Executa o pipeline completo:
        Evento → Supervisores → Decision Tree → Monte Carlo → Relatório
    """

    def __init__(self) -> None:
        self.supervisor_org  = SupervisorOrganizationalEnvironment()
        self.supervisor_risk = SupervisorRiskManagement()
        self.supervisor_cont = SupervisorContinuityRecovery()

    async def process_event(
        self,
        event: EventModel,
        use_llm_enhancement: bool = True,
    ) -> Dict:
        """
        Processa um evento

        Returns
        -------
        dict com chaves:
          status, mean_probability, mean_probability_pct, priority,
          iso_22324, confidence_interval_95, percentiles,
          pearson_correlations, std_deviation,
          sentiment, risk_agents, organizational_context,
          crisis_scenarios, decision_tree, conformity_factor,
          analysis_summary, low_risk_assessment
        """
        try:
            log.info("═" * 72)
            log.info("C2M — INÍCIO DO PIPELINE")
            log.info("═" * 72)

            log.info("ESTÁGIO 1: Extração via supervisores")

            # Supervisor 1: Sentimento + sinais de crise
            sentiment: SentimentAnalysisC2M = await self.supervisor_org.analyze_event(event)
            crisis_signals = self.supervisor_org.detect_crisis_signals(
                sentiment, event.type, event.details
            )
            log.info(
                "  Sup.1 → sentimento=%s polarity=%.3f keywords=%d",
                sentiment.interpretation,
                sentiment.polarity,
                len(crisis_signals.get("keywords_found", [])),
            )

            # Supervisor 3: Contexto organizacional (inclui histórico de eventos)
            context: OrganizationalContextC2M = await self.supervisor_cont.collect_organizational_context()
            log.info(
                "  Sup.3 → maturidade=%.1f/5.0 planos=crise:%s continuidade:%s "
                "historico_incidentes=%d",
                context.maturity_level,
                "✓" if context.has_crisis_plan else "✗",
                "✓" if context.has_continuity_plan else "✗",
                context.historical_similar_events,
            )

            # Supervisor 2: Agentes de risco
            risk_agents = await self.supervisor_risk.extract_risk_agents(event, context)
            log.info("  Sup.2 → %d agentes de risco identificados", len(risk_agents))

            # Fator de conformidade C (VectorSearchService) ──────────
            # Constrói o texto de consulta a partir da transcrição ou details
            transcript_text = (
                event.details.get("text_presents_in_audio")
                or event.details.get("transcription")
                or f"{event.type}: {event.details}"
            )
            conformity_factor: float = calculate_conformity(transcript_text, top_k=5)
            log.info("  VectorSearch → conformity_factor=%.4f", conformity_factor)

            log.info("ESTÁGIO 2: Decision Tree")

            is_potential_crisis, decision_score, decision_reasoning = (
                DecisionTreeAnalyzer.evaluate(sentiment, event.type, context)
            )
            decision_result = {
                "is_potential_crisis": is_potential_crisis,
                "confidence_score": round(decision_score, 4),
                "reasoning": decision_reasoning,
            }

            if not is_potential_crisis:
                log.info(
                    "  Score %.3f abaixo do threshold → sem potencial de crise",
                    decision_score,
                )
                return {
                    "status": "success",
                    "mean_probability": 0.0,
                    "mean_probability_pct": 0.0,
                    "priority": "Baixa",
                    "iso_22324": {"level": "VERDE", "color": "#00AA00", "action": "Monitorar situação"},
                    "std_deviation": 0.0,
                    "confidence_interval_95": {"lower": 0.0, "upper": 0.0},
                    "percentiles": {f"p{k}": 0.0 for k in (10, 25, 50, 75, 90)},
                    "pearson_correlations": {},
                    "conformity_factor": round(conformity_factor, 4),
                    "sentiment": sentiment.to_dict(),
                    "risk_agents": [a.to_dict() for a in risk_agents],
                    "organizational_context": context.to_dict(),
                    "crisis_scenarios": [],
                    "decision_tree": decision_result,
                    "analysis_summary": (
                        f"Evento analisado. Score de crise: {decision_score:.3f}. "
                        "Sem potencial imediato de crise cibernética."
                    ),
                    "crisis_signals": crisis_signals,
                    "low_risk_assessment": True,
                }

            log.info("ESTÁGIO 3: Monte Carlo (N=%d simulações)", 50_000)

            mc_result: MonteCarloResult = MonteCarloProbabilityCalculator.run_simulation(
                context=context,
                sentiment_polarity=sentiment.polarity,
                conformity_factor=conformity_factor,
            )

            log.info("ESTÁGIO 4: Geração de sumário")

            analysis_summary = await self._generate_summary(
                event=event,
                sentiment=sentiment,
                risk_agents=risk_agents,
                mc=mc_result,
                context=context,
                conformity_factor=conformity_factor,
                use_llm=use_llm_enhancement,
            )

            log.info("═" * 72)
            log.info(
                "C2M — CONCLUÍDO: P̄=%.4f ISO=%s",
                mc_result.mean_probability,
                mc_result.iso_level,
            )

            return {
                "status": "success",
                # Probabilidade
                "mean_probability": mc_result.mean_probability,
                "mean_probability_pct": round(mc_result.mean_probability * 100, 2),
                "std_deviation": mc_result.std_deviation,
                "confidence_interval_95": {
                    "lower": mc_result.ci_95_lower,
                    "upper": mc_result.ci_95_upper,
                },
                "percentiles": mc_result.percentiles,
                "pearson_correlations": mc_result.pearson_correlations,
                # Classificação 
                "priority": mc_result.priority,
                "iso_22324": {
                    "level": mc_result.iso_level,
                    "color": mc_result.iso_color,
                    "action": mc_result.iso_action,
                },
                # Conformidade
                "conformity_factor": round(conformity_factor, 4),
                # Contexto 
                "sentiment": sentiment.to_dict(),
                "risk_agents": [a.to_dict() for a in risk_agents],
                "organizational_context": context.to_dict(),
                "crisis_scenarios": [s.to_dict() for s in mc_result.crisis_scenarios],
                "decision_tree": decision_result,
                "crisis_signals": crisis_signals,
                "analysis_summary": analysis_summary,
                "low_risk_assessment": False,
            }

        except Exception as exc:
            log.error("Erro no pipeline C2M: %s", exc, exc_info=True)
            return {
                "status": "error",
                "error_message": str(exc),
                "mean_probability": 0.0,
                "mean_probability_pct": 0.0,
                "priority": "Desconhecida",
            }

    async def _generate_summary(
        self,
        event: EventModel,
        sentiment: SentimentAnalysisC2M,
        risk_agents: list,
        mc: MonteCarloResult,
        context: OrganizationalContextC2M,
        conformity_factor: float,
        use_llm: bool = True,
    ) -> str:
        """Gera sumário estruturado e, opcionalmente, enriquece com LLM."""

        top_pearson = sorted(
            ((k, v) for k, v in mc.pearson_correlations.items() if v == v),  # exclui NaN
            key=lambda kv: abs(kv[1]),
            reverse=True,
        )[:3]

        summary = (
            f"ANÁLISE C2M — RESUMO EXECUTIVO\n"
            f"{'=' * 72}\n\n"
            f"EVENTO:   {event.type}\n"
            f"ORIGEM:   {event.origin}\n\n"
            f"PROBABILIDADE DE CRISE CIBERNÉTICA:  {mc.mean_probability:.2%}\n"
            f"  σ (desvio padrão):                 {mc.std_deviation:.4f}\n"
            f"  IC 95%: [{mc.ci_95_lower:.4f}, {mc.ci_95_upper:.4f}]\n"
            f"  Percentis: "
            + " | ".join(f"{k}={v:.4f}" for k, v in mc.percentiles.items())
            + "\n\n"
            f"CLASSIFICAÇÃO ISO 22324:\n"
            f"  Nível:  {mc.iso_level}\n"
            f"  Cor:    {mc.iso_color}\n"
            f"  Ação:   {mc.iso_action}\n"
            f"  Prioridade: {mc.priority}\n\n"
            f"FATOR DE CONFORMIDADE (C):  {conformity_factor:.4f}\n"
            f"  (0 = alinhado às políticas | 1 = divergente)\n\n"
            f"SENTIMENTO:  {sentiment.interpretation} "
            f"(polarity={sentiment.polarity:.3f}, subjectivity={sentiment.subjectivity:.3f})\n\n"
            f"PRINCIPAIS DRIVERS DE RISCO (Correlação de Pearson):\n"
        )
        for var, r in top_pearson:
            summary += f"  {var}: r={r:.4f}\n"

        summary += f"\nAGENTES DE RISCO IDENTIFICADOS: {len(risk_agents)}\n"
        for i, agent in enumerate(risk_agents[:5], 1):
            summary += (
                f"  {i}. {agent.name} ({agent.category}) "
                f"— severidade={agent.severity:.1%}\n"
            )
        if len(risk_agents) > 5:
            summary += f"  ... e mais {len(risk_agents) - 5} agentes.\n"

        summary += (
            f"\nCONTEXTO ORGANIZACIONAL (ISO 22325):\n"
            f"  Maturidade:         {context.maturity_level}/5.0\n"
            f"  Plano de Riscos:    {'✓' if context.has_risk_plan else '✗'}\n"
            f"  Plano de Crise:     {'✓' if context.has_crisis_plan else '✗'}\n"
            f"  Continuidade:       {'✓' if context.has_continuity_plan else '✗'}\n"
            f"  Recuperação:        {'✓' if context.has_recovery_plan else '✗'}\n"
            f"  Governança Formal:  {'✓' if context.formal_governance else '✗'}\n"
            f"  Incidentes similares (histórico): {context.historical_similar_events}\n\n"
            f"CONFORMIDADE: ISO 22361 | ISO 31000 | ISO 22324 | ISO 22325 | LGPD\n"
        )

        if use_llm:
            try:
                prompt = (
                    "Baseado na seguinte análise C2M, gere um sumário executivo profissional "
                    "em português, com interpretação, recomendações de ação imediata e próximos "
                    f"passos. Tom formal e conciso.\n\n{summary}"
                )
                enriched = await llama_api_call(prompt)
                if enriched:
                    return enriched
            except Exception as exc:
                log.debug("LLM indisponível, usando sumário estruturado: %s", exc)

        return summary
