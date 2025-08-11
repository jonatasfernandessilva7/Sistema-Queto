import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.AiServices.AiModels import EventModel
from src.AiServices.AiMemory import (
    AiAddingEventHistory,
    AiCompareEventsHistory,
)
from src.AiServices.services.AiAnswerService import AiReactiveAnswer, AiDeliberativePlanning
from src.AiServices.AiApprenticeship import AiClassifyEvent
from src.AiServices.services.AiReportsService import AiGeneretadReportsWithLlama, AiSaveReports
from src.backend.utils.EmailUtils import sendEmailReportLessAttachment

load_dotenv()

async def receiveEvent(evento: EventModel):

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        AiAddingEventHistory({"evento": evento.model_dump(), "timestamp": timestamp})

        aiReactiveAnswer = AiReactiveAnswer(evento)
        aiDeliberativePlann = AiDeliberativePlanning(evento)
        priority = await AiClassifyEvent(evento)

        similarMessage, similarEvent = AiCompareEventsHistory(evento)

        relatorio = await AiGeneretadReportsWithLlama(evento, aiReactiveAnswer, aiDeliberativePlann, priority)
        aiReport = AiSaveReports(relatorio, timestamp, priority)
        sendEmailReportLessAttachment(aiReport, os.getenv("EMAIL_DESTINO"))

        return JSONResponse(content={
            "status":200,
            "AI_reactive_answer": aiReactiveAnswer,
            "AI_deliberative_plan": aiDeliberativePlann,
            "priority": priority,
            "AI_report": aiReport,
            "similarity": similarMessage,
            "similar_event": similarEvent,
            "timestamp": timestamp
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
