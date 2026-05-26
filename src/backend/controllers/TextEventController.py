import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.core.models import EventModel, add_event_to_history, compare_events_with_history
from src.api.services.analysis import AiReactiveAnswer, AiDeliberativePlanning, AiClassifyEvent
from src.api.services.reports import AiGeneretadReportsWithLlama, AiSaveReports
from src.core.utils import sendEmailReportLessAttachment

load_dotenv()

async def receiveEvent(evento: EventModel):

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        add_event_to_history({"event": evento.model_dump(), "timestamp": timestamp})

        aiReactiveAnswer = AiReactiveAnswer(evento)
        aiDeliberativePlann = AiDeliberativePlanning(evento)
        priority = await AiClassifyEvent(evento)

        similarMessage, similarEvent = compare_events_with_history(evento)

        relatorio = await AiGeneretadReportsWithLlama(evento, aiReactiveAnswer, aiDeliberativePlann, priority)
        aiReport = AiSaveReports(relatorio, timestamp, priority)
        sendEmailReportLessAttachment(aiReport, os.getenv("DESTINATION_EMAIL"))

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
