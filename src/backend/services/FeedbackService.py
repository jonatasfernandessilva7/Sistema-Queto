from src.backend.repository.GenericsRepository import save_human_feedback
from src.AiServices.services.AIFeedbackService import Feedback

async def service_submit_feedback(feedback: Feedback):
    # a prioridade é a classificação do evento: alto, moderado, baixo etc.
    # a classificação é o tipo de evento: desastre natural, violação de imagem etc.
    # como recuperar isso da llm?
     try:
        save_human_feedback(
            feedback.event_id, 
            None,
            None,
            feedback.human_classification, 
            feedback.human_priority, 
            feedback.comment
            )
        return True

     except Exception as e:
         print(e)
         return False