"""
Supervisor 3: Continuidade e Recuperação
Monitora capacidade de continuidade e recuperação da organização

Integra com:
- DocumentAnalysisService (análise de PDFs/documentos)
- EventHistory (histórico de eventos)
"""

import logging
from pathlib import Path
from typing import Dict, Optional
from src.core.config.settings import Settings
from src.agents.orchestrator.C2M_Models import OrganizationalContextC2M
from src.api.services.analysis import extract_text

log = logging.getLogger(__name__)


class SupervisorContinuityRecovery:
    """
    Agente Supervisor 3: Continuidade e Recuperação
    
    Responsabilidades:
    1. Coletar contexto organizacional real de documentos
    2. Avaliar maturidade organizacional (ISO 22325)
    3. Validar existência de planos (risco, crise, continuidade, recuperação)
    4. Calcular score de resiliência
    """
    
    def __init__(self):
        self.name = "Supervisor Continuidade e Recuperação"
        self.monitors = [
            "Plano de Desastre (DR)",
            "Plano de Continuidade (BC)",
            "Simulações e Testes",
            "Backups e Replicação"
        ]
        
        self.uploads_dir = Settings.UPLOADS_DIR
        self.cache = {}
    
    async def collect_organizational_context(self) -> OrganizationalContextC2M:
        """
        Coleta contexto organizacional real
        
        Estratégia:
        1. Procurar arquivos em UPLOADS_DIR
        2. Extrair informações de documentos
        3. Calcular maturidade
        4. Validar planos
        
        Retorna: OrganizationalContextC2M com dados reais
        """
        
        # Verificar cache primeiro
        if "context_cache" in self.cache:
            log.info("Retornando contexto do cache")
            return self.cache["context_cache"]
        
        context = OrganizationalContextC2M(
            maturity_level=await self._extract_maturity_level(),
            has_risk_plan=await self._check_plan_exists("risk"),
            has_crisis_plan=await self._check_plan_exists("crisis"),
            has_continuity_plan=await self._check_plan_exists("continuity"),
            has_recovery_plan=await self._check_plan_exists("recovery"),
            historical_similar_events=await self._count_similar_events(),
            formal_governance=await self._check_formal_governance()
        )
        
        # Cache por 1 hora (em produção, usar TTL)
        self.cache["context_cache"] = context
        
        log.info(f"""
        ════════════════════════════════════════════════════
        CONTEXTO ORGANIZACIONAL COLETADO:
        ════════════════════════════════════════════════════
        Maturidade: {context.maturity_level}/5.0 (ISO 22325)
        Plano de Riscos: {'✓' if context.has_risk_plan else '✗'}
        Plano de Crise: {'✓' if context.has_crisis_plan else '✗'}
        Plano de Continuidade: {'✓' if context.has_continuity_plan else '✗'}
        Plano de Recuperação: {'✓' if context.has_recovery_plan else '✗'}
        Governança Formal: {'✓' if context.formal_governance else '✗'}
        Eventos Similares (histórico): {context.historical_similar_events}
        ════════════════════════════════════════════════════
        """)
        
        return context
    
    async def _extract_maturity_level(self) -> float:
        """
        Extrai nível de maturidade (1-5) baseado em:
        1. Documento "A_maturity_model.pdf" ou similar
        2. Presença e qualidade de planos
        
        Retorna: float entre 1.0 e 5.0
        """
        
        # Procurar arquivo de modelo de maturidade
        maturity_files = [
            "A_maturity_model.pdf",
            "maturity_model.pdf",
            "modelo_maturidade.pdf",
            "capability_assessment.pdf"
        ]
        
        if not self.uploads_dir.exists():
            log.warning(f"Diretório UPLOADS não encontrado: {self.uploads_dir}")
            return 2.0  # Default: baixa maturidade
        
        for maturity_file in maturity_files:
            file_path = self.uploads_dir / maturity_file
            if file_path.exists():
                try:
                    text = await self._safe_extract_text(file_path)
                    maturity = self._parse_maturity_from_text(text)
                    if maturity > 0:
                        log.info(f"Maturidade extraída de {maturity_file}: {maturity}")
                        return maturity
                except Exception as e:
                    log.warning(f"Erro ao processar {maturity_file}: {e}")
        
        # Fallback: inferir de planos presentes
        plan_count = sum([
            await self._check_plan_exists("risk"),
            await self._check_plan_exists("crisis"),
            await self._check_plan_exists("continuity"),
            await self._check_plan_exists("recovery")
        ])
        
        # 0 planos = 1.0, 1= 2.0, 2=3.0, 3=4.0, 4=5.0
        inferred_maturity = 1.0 + (plan_count * 1.0)
        log.info(f"Maturidade inferida de planos presentes: {inferred_maturity}")
        
        return min(5.0, inferred_maturity)
    
    async def _check_plan_exists(self, plan_type: str) -> bool:
        """Verifica se um tipo de plano existe"""
        
        plan_keywords = {
            "risk": ["risco", "risk", "iso 31000", "risk management", "gestão de riscos"],
            "crisis": ["crise", "crisis", "cyber crisis", "crise cibernética", "plano de crise"],
            "continuity": ["continuidade", "continuity", "bc", "business continuity", "plano de continuidade"],
            "recovery": ["recuperação", "recovery", "dr", "disaster recovery", "plano de recuperação"]
        }
        
        if plan_type not in plan_keywords:
            return False
        
        keywords = plan_keywords[plan_type]
        
        if not self.uploads_dir.exists():
            return False
        
        for file_path in self.uploads_dir.glob("*"):
            if file_path.suffix.lower() not in ['.pdf', '.docx', '.txt', '.doc']:
                continue
            
            try:
                text = await self._safe_extract_text(file_path)
                text_lower = text.lower()
                
                if any(keyword in text_lower for keyword in keywords):
                    log.info(f"Plano de {plan_type} encontrado: {file_path.name}")
                    return True
            except Exception as e:
                log.debug(f"Erro ao verificar {file_path.name}: {e}")
                continue
        
        return False
    
    async def _check_formal_governance(self) -> bool:
        """Verifica se há política formal de governança"""
        
        governance_keywords = [
            "governança", "governance", "iso 22325", "capability assessment",
            "política de segurança", "security policy", "comitê", "committee"
        ]
        
        if not self.uploads_dir.exists():
            return False
        
        for file_path in self.uploads_dir.glob("*"):
            if file_path.suffix.lower() not in ['.pdf', '.docx', '.txt', '.doc']:
                continue
            
            try:
                text = await self._safe_extract_text(file_path)
                text_lower = text.lower()
                
                if any(keyword in text_lower for keyword in governance_keywords):
                    log.info(f"Governança formal detectada em: {file_path.name}")
                    return True
            except:
                continue
        
        return False
    
    async def _count_similar_events(self) -> int:
        """
        Conta eventos similares no histórico
        
        TODO: Integrar com EventRepository para consultar DB
        """
        # Por enquanto, retornar 0 (será implementado com DB)
        return 0
    
    async def _safe_extract_text(self, file_path: Path) -> str:
        """Extrai texto de arquivo com erro handling"""
        try:
            return extract_text(str(file_path))
        except Exception as e:
            log.debug(f"Erro ao extrair texto de {file_path}: {e}")
            return ""
    
    @staticmethod
    def _parse_maturity_from_text(text: str) -> float:
        """
        Procura por nível de maturidade explícito no texto
        
        Padrões: "nível 3", "level 3", "maturity level: 3"
        """
        import re
        
        text_lower = text.lower()
        
        # Procurar padrões como "nível 3", "level 3"
        patterns = [
            r'nível\s+(\d)',
            r'level\s+(\d)',
            r'maturity\s+level[\s:]+(\d)',
            r'nível de maturidade[\s:]+(\d)',
            r'capability level[\s:]+(\d)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                level = int(match.group(1))
                if 1 <= level <= 5:
                    return float(level)
        
        return 0.0  # Não encontrou
    
    def assess_resilience(self, context: OrganizationalContextC2M) -> float:
        """
        Avalia score de resiliência (0-1)
        
        Fatores:
        - Existência de planos (40%)
        - Nível de maturidade (40%)
        - Governança formal (20%)
        
        Retorna: 0.0 a 1.0
        """
        
        # Fator 1: Planos (0-0.4)
        plans = [
            context.has_risk_plan,
            context.has_crisis_plan,
            context.has_continuity_plan,
            context.has_recovery_plan
        ]
        plans_score = sum(plans) / len(plans) * 0.4
        
        # Fator 2: Maturidade (0-0.4)
        maturity_normalized = context.maturity_level / 5.0
        maturity_score = maturity_normalized * 0.4
        
        # Fator 3: Governança (0-0.2)
        governance_score = 0.2 if context.formal_governance else 0.0
        
        total = plans_score + maturity_score + governance_score
        
        return min(1.0, total)


# Para facilitar uso
async def collect_context() -> OrganizationalContextC2M:
    """Função helper para coletar contexto"""
    supervisor = SupervisorContinuityRecovery()
    return await supervisor.collect_organizational_context()
