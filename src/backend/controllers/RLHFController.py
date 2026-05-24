"""
RLHF Controller
API endpoints para o sistema de feedback com aprendizado reforçado
"""

import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from src.AiServices.services.RLHFFeedbackService import RLHFFeedbackService
from src.backend.models.ReportFeedback import (
    ReportFeedback,
    ReportFeedbackCreate,
    FeedbackStats
)

log = logging.getLogger(__name__)

# Instância global do serviço
_rlhf_service: Optional[RLHFFeedbackService] = None


def get_rlhf_service() -> RLHFFeedbackService:
    """Obtém instância do serviço RLHF"""
    global _rlhf_service
    if _rlhf_service is None:
        _rlhf_service = RLHFFeedbackService()
    return _rlhf_service


async def submit_report_feedback(feedback_data: ReportFeedbackCreate) -> JSONResponse:
    """
    Endpoint para enviar feedback de um relatório C2M
    
    POST /v1/u/rlhf/feedback
    
    Args:
        feedback_data: Dados do feedback
        
    Returns:
        JSONResponse com feedback armazenado
    """
    try:
        service = get_rlhf_service()
        feedback = service.receive_feedback(feedback_data)
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "Feedback received and stored",
                "feedback_id": feedback.id,
                "report_id": feedback.report_id
            }
        )
    except Exception as e:
        log.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


async def get_feedback(feedback_id: str) -> JSONResponse:
    """
    Obtém um feedback específico
    
    GET /v1/u/rlhf/feedback/{feedback_id}
    
    Args:
        feedback_id: ID do feedback
        
    Returns:
        JSONResponse com dados do feedback
    """
    try:
        service = get_rlhf_service()
        feedback = service.get_feedback(feedback_id)
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "feedback": feedback.model_dump()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving feedback: {str(e)}"
        )


async def get_report_feedback_stats(report_id: str) -> JSONResponse:
    """
    Obtém estatísticas de feedback para um relatório
    
    GET /v1/u/rlhf/reports/{report_id}/feedback-stats
    
    Args:
        report_id: ID do relatório
        
    Returns:
        JSONResponse com estatísticas
    """
    try:
        service = get_rlhf_service()
        stats = service.get_feedback_stats(report_id)
        
        if not stats:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_feedback",
                    "message": f"No feedback yet for report {report_id}"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "report_id": report_id,
                "feedback_stats": {
                    "total_feedbacks": stats.total_feedbacks,
                    "accuracy_rate": stats.accuracy_rate,
                    "probability_accuracy": stats.probability_accuracy,
                    "priority_accuracy": stats.priority_accuracy,
                    "risk_agents_accuracy": stats.risk_agents_accuracy,
                    "sentiment_accuracy": stats.sentiment_accuracy
                }
            }
        )
    except Exception as e:
        log.error(f"Error getting feedback stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting feedback stats: {str(e)}"
        )


async def get_adjustment_history(limit: int = 50) -> JSONResponse:
    """
    Obtém histórico de ajustes de peso
    
    GET /v1/u/rlhf/adjustments?limit=50
    
    Args:
        limit: Número máximo de ajustes a retornar
        
    Returns:
        JSONResponse com histórico
    """
    try:
        service = get_rlhf_service()
        adjustments = service.get_adjustment_history(limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "total_adjustments": len(adjustments),
                "adjustments": [
                    {
                        "component": adj.component,
                        "current_value": adj.current_value,
                        "adjustment_amount": adj.adjustment_amount,
                        "new_value": adj.new_value,
                        "reason": adj.reason,
                        "confidence": adj.confidence,
                        "timestamp": adj.timestamp.isoformat()
                    }
                    for adj in adjustments
                ]
            }
        )
    except Exception as e:
        log.error(f"Error getting adjustment history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting adjustment history: {str(e)}"
        )


async def get_current_weights() -> JSONResponse:
    """
    Obtém pesos atuais do sistema C2M
    
    GET /v1/u/rlhf/weights
    
    Returns:
        JSONResponse com pesos atuais
    """
    try:
        service = get_rlhf_service()
        weights = service.weight_manager.get_all_weights()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "weights": weights
            }
        )
    except Exception as e:
        log.error(f"Error getting weights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting weights: {str(e)}"
        )


async def trigger_feedback_processing(min_feedbacks: int = 10) -> JSONResponse:
    """
    Dispara o processamento de feedback e ajuste de pesos (RLHF loop)
    
    POST /v1/u/rlhf/process?min_feedbacks=10
    
    Args:
        min_feedbacks: Número mínimo de feedbacks para disparar
        
    Returns:
        JSONResponse com resultados do processamento
    """
    try:
        service = get_rlhf_service()
        result = service.process_and_apply_adjustments(min_feedbacks)
        
        status_code = 200 if result["status"] == "completed" else 202
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": result["status"],
                "feedbacks_analyzed": result["feedbacks_analyzed"],
                "adjustments_applied": result["adjustments_applied"],
                "errors": result["errors"]
            }
        )
    except Exception as e:
        log.error(f"Error processing feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        )


async def reset_weights_to_defaults() -> JSONResponse:
    """
    Reseta pesos para valores padrão
    
    POST /v1/u/rlhf/reset-weights
    
    Returns:
        JSONResponse confirmando reset
    """
    try:
        service = get_rlhf_service()
        success = service.weight_manager.reset_to_defaults()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset weights"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Weights reset to defaults",
                "weights": service.weight_manager.get_all_weights()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error resetting weights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting weights: {str(e)}"
        )
