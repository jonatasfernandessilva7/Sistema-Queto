"""
Supervisor 2: Gestão de Riscos
Monitora planos de risco e identifica agentes de risco

Integra com:
- RiskAnalysisAgents (monitoring_app, response_app, plan_app)
- DocumentAnalysisService (análise de documentos)
"""

import logging
from typing import List, Dict
from src.core.models import EventModel
from src.core.config.settings import Settings
from src.agents.orchestrator.C2M_Models import RiskAgentC2M, OrganizationalContextC2M

log = logging.getLogger(__name__)


class SupervisorRiskManagement:
    """
    Agente Supervisor 2: Gestão de Riscos
    
    Responsabilidades:
    1. Identificar agentes de risco do evento
    2. Calcular severidade de cada agente
    3. Mapear cadeia de impactos
    4. Validar plano de resposta a riscos
    """
    
    def __init__(self):
        self.name = "Supervisor Gestão de Riscos"
        self.monitors = [
            "Plano de Riscos (ISO 31000)",
            "Resposta a Riscos",
            "Monitoramento e Controle",
            "Métricas de Risco"
        ]
    
    async def extract_risk_agents(self, 
                                  event: EventModel,
                                  context: OrganizationalContextC2M) -> List[RiskAgentC2M]:
        """
        Identifica agentes de risco baseado em:
        1. Tipo do evento
        2. Contexto organizacional
        3. Severidade indicada
        
        Retorna: List[RiskAgentC2M] com cada risco identificado
        """
        
        agents = []
        event_type = event.type.lower()
        
        # ============================================================================
        # CATEGORIA 1: RISCOS AUTOMÁTICOS POR TIPO DE EVENTO
        # ============================================================================
        
        # Tipos de evento críticos que indicam riscos específicos
        if any(term in event_type for term in ["ataque", "attack", "intrusion", "intrusão"]):
            agents.extend([
                RiskAgentC2M(
                    name="Comprometimento de Segurança",
                    category="technological",
                    severity=0.85,
                    impact_chain=["Acesso Não-Autorizado", "Roubo de Dados", "Sistema Comprometido"],
                    mitigation="Isolar sistemas afetados, executar análise forense, restaurar de backup"
                ),
                RiskAgentC2M(
                    name="Perda de Integridade de Dados",
                    category="technological",
                    severity=0.75,
                    impact_chain=["Dados Corrompidos", "Inconsistência", "Falha em Operações"],
                    mitigation="Validar integridade, processos de reconciliação, teste de backup"
                )
            ])
        
        if any(term in event_type for term in ["falha", "failure", "crash", "indisponível"]):
            agents.extend([
                RiskAgentC2M(
                    name="Indisponibilidade de Serviço",
                    category="technological",
                    severity=0.8,
                    impact_chain=["Operações Paradas", "Perda de Receita", "Impacto Reputacional"],
                    mitigation="Ativar plano de continuidade, failover automático, comunicação com stakeholders"
                ),
                RiskAgentC2M(
                    name="Falta de Redundância",
                    category="organizational",
                    severity=0.6,
                    impact_chain=["Ponto Único de Falha", "Indisponibilidade Prolongada"],
                    mitigation="Implementar redundância, disaster recovery, testes regulares"
                )
            ])
        
        if any(term in event_type for term in ["vazamento", "leak", "exposição", "exposure", "breach"]):
            agents.extend([
                RiskAgentC2M(
                    name="Exposição de Dados Sensíveis",
                    category="reputational",
                    severity=0.9,
                    impact_chain=["Notificação Legal", "Sansão Regulatória (LGPD)", "Perda de Confiança"],
                    mitigation="Notificação imediata, investigação, comunicação de crise, suporte a afetados"
                ),
                RiskAgentC2M(
                    name="Não-Conformidade Regulatória",
                    category="regulatory",
                    severity=0.8,
                    impact_chain=["Multa Regulatória", "Penalidade Legal", "Reputação Danificada"],
                    mitigation="Reportar à autoridade competente, documentar resposta, consulta legal"
                )
            ])
        
        # ============================================================================
        # CATEGORIA 2: RISCOS ORGANIZACIONAIS (BASEADOS E CONTEXTO)
        # ============================================================================
        
        # Se contexto organizacional é fraco
        if not context.has_risk_plan:
            agents.append(RiskAgentC2M(
                name="Ausência de Plano de Riscos",
                category="governance",
                severity=0.7,
                impact_chain=["Resposta Desorganizada", "Tempos Ineficientes", "Escalação Desnecessária"],
                mitigation="Estabelecer plano de riscos conforme ISO 31000"
            ))
        
        if not context.has_crisis_plan:
            agents.append(RiskAgentC2M(
                name="Falta de Plano de Crise",
                category="governance",
                severity=0.8,
                impact_chain=["Resposta Improviso", "Comunicação Confusa", "Decisões Lentas"],
                mitigation="Implementar plano de crise, treinar time, exercícios regulares"
            ))
        
        if not context.has_continuity_plan:
            agents.append(RiskAgentC2M(
                name="Ausência de Plano de Continuidade",
                category="governance",
                severity=0.75,
                impact_chain=["Recuperação Lenta", "Prolongamento de Crise", "Impacto Maior"],
                mitigation="Desenvolver BC/DR plan, testar periodicamente"
            ))
        
        if context.maturity_level < 2:
            agents.append(RiskAgentC2M(
                name="Maturidade Organizacional Muito Baixa",
                category="organizational",
                severity=0.7,
                impact_chain=["Capacidade Resposta Reduzida", "Falta de Recursos", "Processos Ineficientes"],
                mitigation="Implementar programa de maturidade conforme ISO 22325"
            ))
        elif context.maturity_level < 3:
            agents.append(RiskAgentC2M(
                name="Maturidade Organizacional Baixa",
                category="organizational",
                severity=0.5,
                impact_chain=["Capacidade Resposta Limitada", "Processos Começando"],
                mitigation="Incrementar maturidade através de treinamentos e processos"
            ))
        
        if context.formal_governance is False:
            agents.append(RiskAgentC2M(
                name="Falta de Governança Formal",
                category="governance",
                severity=0.6,
                impact_chain=["Falta de Autoridade", "Procrastinação", "Inconsistência"],
                mitigation="Estabelecer estrutura de governança, definir roles e responsabilidades"
            ))
        
        # ============================================================================
        # CATEGORIA 3: RISCOS GENÉRICOS (SEMPRE PRESENTES)
        # ============================================================================
        
        # Sempre adicionar riscos genéricos se ainda não estão presentes
        if not any("Falta de Visibilidade" in a.name for a in agents):
            agents.append(RiskAgentC2M(
                name="Falta de Visibilidade de Eventos",
                category="technological",
                severity=0.5,
                impact_chain=["Detecção Tardia", "Tempo de Resposta Maior"],
                mitigation="Melhorar SIEM, centralizar logs, alertas inteligentes"
            ))
        
        log.info(f"Identificados {len(agents)} agentes de risco para evento: {event_type}")
        return agents
    
    def calculate_risk_score(self, agents: List[RiskAgentC2M]) -> float:
        """
        Calcula score de risco agregado (0-1)
        
        Método: média ponderada de severidade
        """
        if not agents:
            return 0.0
        
        total_severity = sum(agent.severity for agent in agents)
        return min(1.0, total_severity / len(agents))
    
    async def validate_response_plan(self, event: EventModel) -> Dict:
        """
        Valida se há plano de resposta apropriado
        
        Retorna Dict com status de validação
        """
        
        # TODO: Integrar com RiskAnalysisAgents.response_app
        # Por agora, retornar validação básica
        
        return {
            "has_response_plan": True,
            "is_adequate": True,
            "recommendations": []
        }


# Import Dict para type hints
from typing import Dict
