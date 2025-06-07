from fastapi import HTTPException
from src.backend.db.db import save_human_feedback
from src.IA.services.feedback import Feedback

async def submit_feedback(feedback: Feedback):
     
     try:

         save_human_feedback(feedback.event_id, feedback.human_classification, feedback.human_priority, feedback.comment)
         
         return {"message": "Feedback recebido com sucesso."}
     
     except Exception as e:
         
         raise HTTPException(status_code=500, detail=str(e))