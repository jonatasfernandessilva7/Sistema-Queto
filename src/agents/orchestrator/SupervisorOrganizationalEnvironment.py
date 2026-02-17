"""
Supervisor 1: Ambiente Organizacional
Monitora comunicação, comportamento e emoções organizacionais

Integra com:
- EmotionAgent (análise de emoção via TextBlob)
- Behavioral_analysis_agent (análise de padrões de comportamento)
"""

import os
import json
import logging
from typing import Dict, Optional
from langchain_core.messages import HumanMessage

from src.core.models import EventModel
from src.agents.orchestrator.C2M_Models import SentimentAnalysisC2M
from src.api.services.analysis import emotionAnalysis

log = logging.getLogger(__name__)


class SupervisorOrganizationalEnvironment:
    """
    Agente Supervisor 1: Monitora Ambiente Organizacional
    
    Responsabilidades:
    1. Análise de sentimento do evento/comunicação
    2. Detecção de padrões comportamentais anômalos
    3. Identificação de sinais de crise organizacional
    """
    
    def __init__(self):
        self.name = "Supervisor Ambiente Organizacional"
        self.monitors = [
            "Áudio de Reuniões",
            "Mensagens Eletrônicas",
            "Grupos de Discussão",
            "Identidade Comportamental"
        ]
    
    async def analyze_event(self, event: EventModel) -> SentimentAnalysisC2M:
        """
        Analisa evento para extrair sentimento
        
        Entradas:
        - event.type: Tipo do evento
        - event.origin: Origem (áudio, email, sistema)
        - event.details: Detalhes estruturados
        
        Saída:
        - SentimentAnalysisC2M com polarity, subjectivity, interpretation
        """
        
        # Construir texto para análise
        event_text = self._build_analysis_text(event)
        
        try:
            # Tentar usar EmotionAnalysis service
            emotion_result = emotionAnalysis(event_text)
            
            if emotion_result and "error" not in emotion_result:
                # Integrar emoção com análise de sentimento
                sentiment = SentimentAnalysisC2M.analyze(event_text)
                
                # Ajustar interpretação com base em emoção detectada
                emotion = emotion_result.get("emotion", "").lower()
                if emotion in ["raiva", "medo", "ansiedade", "alarme"]:
                    # Forçar interpretação negativa
                    if sentiment.polarity > -0.1:
                        sentiment.polarity = -0.2
                
                log.info(f"Análise de sentimento: {sentiment.interpretation} (polarity={sentiment.polarity:.2f})")
                return sentiment
            else:
                # Fallback para TextBlob puro
                return SentimentAnalysisC2M.analyze(event_text)
        
        except Exception as e:
            log.warning(f"Erro ao analisar sentimento: {e}. Usando TextBlob puro.")
            return SentimentAnalysisC2M.analyze(event_text)
    
    def detect_crisis_signals(self, 
                             sentiment: SentimentAnalysisC2M, 
                             event_type: str,
                             event_details: Dict) -> Dict:
        """
        Detecta sinais de crise no evento
        
        Checkpoints:
        1. Sentimento muito negativo (polarity < -0.2)
        2. Padrões de palavras-chave de crise
        3. Entidades críticas mencionadas
        
        Retorna Dict com sinais encontrados
        """
        
        signals = {
            "sentiment_critical": sentiment.polarity < -0.2,
            "keywords_found": [],
            "severity_indicators": []
        }
        
        # Palavras-chave de crise cibernética
        crisis_keywords = [
            "ataque", "invasão", "comprometimento", "falha", "indisponibilidade",
            "violação", "breach", "ransomware", "malware", "criptografado",
            "impossível acessar", "sistema parado", "resgate", "exfiltração",
            "roubo", "vazamento", "dados expostos", "segurança", "urgente", "crítico"
        ]
        
        # Construir texto para busca
        event_text = self._build_analysis_text(event_type, event_details).lower()
        
        for keyword in crisis_keywords:
            if keyword in event_text:
                signals["keywords_found"].append(keyword)
        
        # Indicadores de severidade
        if sentiment.polarity < -0.3:
            signals["severity_indicators"].append("sentimento_extremamente_negativo")
        if len(signals["keywords_found"]) >= 3:
            signals["severity_indicators"].append("multiplos_indicadores_crise")
        if any(word in event_text for word in ["urgente", "crítico", "imediato"]):
            signals["severity_indicators"].append("linguagem_urgente")
        
        return signals
    
    @staticmethod
    def _build_analysis_text(event_type: str, event_details: Dict = None) -> str:
        """Constrói texto para análise"""
        if isinstance(event_type, EventModel):
            # Se recebeu EventModel
            event = event_type
            text = f"{event.type} from {event.origin}: "
            if isinstance(event.details, dict):
                text += json.dumps(event.details, ensure_ascii=False)
            else:
                text += str(event.details)
        else:
            # Se recebeu type e details separados
            text = f"{event_type}: "
            if event_details:
                if isinstance(event_details, dict):
                    text += json.dumps(event_details, ensure_ascii=False)
                else:
                    text += str(event_details)
        
        return text[:1000]  # Limitar para performance
