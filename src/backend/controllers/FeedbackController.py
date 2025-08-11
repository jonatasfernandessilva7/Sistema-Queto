from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.backend.services.FeedbackService import service_submit_feedback
from src.AiServices.services.AIFeedbackService import Feedback

async def submit_feedback(feedback: Feedback):
     
     try:
        result = await service_submit_feedback(feedback)
        if not result:
           return {"message": "your feedback not send"}
        return JSONResponse(content={"status":200, "message": "receives feedback."})
     
     except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))