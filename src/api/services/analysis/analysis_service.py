"""
AI Analysis Services - consolidated from multiple sources.
Includes emotion analysis, answer generation, event classification, and more.
"""

from src.AiServices.services.AiAnswerService import (
    AiReactiveAnswer,
    AiDeliberativePlanning,
    gerar_resposta_llama_api
)
from src.AiServices.services.AiEmotionAnalysisService import (
    emotionAnalysis
)
from src.AiServices.AiApprenticeship import AiClassifyEvent
from src.backend.services.DocumentAnalysisService import (
    extract_text,
    extract_tables,
    extract_images,
    resume_text
)

__all__ = [
    # Answer/Response services
    'AiReactiveAnswer',
    'AiDeliberativePlanning',
    'gerar_resposta_llama_api',
    # Emotion analysis
    'emotionAnalysis',
    # Event classification
    'AiClassifyEvent',
    # Document analysis
    'extract_text',
    'extract_tables',
    'extract_images',
    'resume_text',
]
