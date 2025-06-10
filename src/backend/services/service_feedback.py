from src.backend.db.db import save_human_feedback
from src.IA.services.feedback import Feedback

async def service_submit_feedback(feedback: Feedback):

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