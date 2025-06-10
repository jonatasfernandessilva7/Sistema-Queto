from fastapi import HTTPException
from src.backend.services.service_feedback import service_submit_feedback
from src.IA.services.feedback import Feedback

async def submit_feedback(feedback: Feedback):
     
     try:

        resultado = await service_submit_feedback(feedback)

        if not resultado:
           return {"message": "seu feedback não foi enviado"}
         
        return {"message": "Feedback recebido com sucesso."}
     
     except Exception as e:
         
         raise HTTPException(status_code=500, detail=str(e))