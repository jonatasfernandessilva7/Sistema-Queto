import logging
from src.backend.repository.GenericsRepository import save_human_feedback
from src.AiServices.services.AIFeedbackService import Feedback

log = logging.getLogger(__name__)

async def service_submit_feedback(feedback: Feedback):
    """
    Process and store human feedback for an event.
    
    Args:
        feedback: Feedback object containing event_id, classification, priority, and comment
        
    Returns:
        bool: True if feedback was saved successfully, False otherwise
        
    Raises:
        ValueError: If feedback object is invalid
    """
    try:
        # Validate feedback object
        if not feedback or not feedback.event_id:
            log.warning("Feedback received without valid event_id")
            raise ValueError("event_id is required")
        
        # Validate priority and classification if provided
        if feedback.human_priority:
            valid_priorities = ["Baixa", "Moderada", "Alta", "Crítico", "Desconhecida"]
            if feedback.human_priority not in valid_priorities:
                log.warning(f"Invalid priority level: {feedback.human_priority}")
                raise ValueError(f"Invalid priority level. Must be one of {valid_priorities}")
        
        if feedback.comment and len(feedback.comment) > 5000:
            log.warning("Feedback comment exceeds maximum length")
            raise ValueError("Comment cannot exceed 5000 characters")
        
        # Save feedback to database
        save_human_feedback(
            feedback.event_id, 
            None,  # classification (to be filled if needed)
            None,  # another parameter
            feedback.human_classification, 
            feedback.human_priority, 
            feedback.comment
        )
        
        log.info(f"Feedback successfully saved for event {feedback.event_id}")
        return True

    except ValueError as e:
        log.warning(f"Validation error in feedback: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error saving feedback: {e}")
        return False