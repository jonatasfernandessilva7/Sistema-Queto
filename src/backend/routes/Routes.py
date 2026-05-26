import os
import sys
import uuid
import asyncio
import datetime
import aiofiles
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import List
from scipy.io import wavfile
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)

from src.backend.controllers import (
    DocumentController,
    MemoryStateController,
    ClusterController,
    TextEventController,
    FeedbackController,
    DocumentAnalysisController,
    ReportsController,
    AudioController,
    RLHFController
)

from src.core.models import EventModel
from src.api.services.feedback import Feedback
from src.backend.models.ReportFeedback import ReportFeedbackCreate

executor = ThreadPoolExecutor(max_workers=4)

router = APIRouter(
    prefix="/v1"
)

@router.delete("/u/docs/{doc_id}")
def delete_doc_id(doc_id: int):
    return DocumentController.delete_document_controller(doc_id)

@router.post("/u/feedback")
async def human_feedback(feedback: Feedback):
    return await FeedbackController.submit_feedback(feedback)

@router.post("/u/docs")
async def upload_file(file: List[UploadFile] = File(...)):
    return await DocumentController.upload_file(file)

@router.post("/u/evento-texto")
async def receivesEvent(evento: EventModel):
    return await TextEventController.receiveEvent(evento)

# record on backend
@router.post("/u/start-recording")
async def receivesAudioMeeting():
    request_idempotency_key = str(uuid.uuid4())
    return await AudioController.startAudioMeeting(idempotency_key=request_idempotency_key)

@router.post("/u/stop-recording")
async def stopAudioMeeting():
    return await AudioController.receivesAndProcessAudio()

#receives on frontend
@router.post("/u/process-audio")
async def processAudio(audio_file: UploadFile = File(...)):
    if not audio_file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser no formato WAV.")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temporaryPath = f"temp_audio_{timestamp}.wav"
    
    try:
        async with aiofiles.open(temporaryPath, "wb") as buffer:
            while content := await audio_file.read(1024):
                await buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    
    q = asyncio.Queue()
    result = await AudioController.receivesAndProcessAudioUploaded(temporaryPath, q=q)
    
    try:
        # Wait for result with 5-minute timeout
        result_final = await asyncio.wait_for(q.get(), timeout=300.0)
    except asyncio.TimeoutError:
        log.error("Timeout waiting for audio processing result")
        raise HTTPException(
            status_code=504,
            detail="Audio processing timed out. Please try again with a shorter audio file."
        )
    finally:
        # Always clean up the temporary file
        if os.path.exists(temporaryPath):
            try:
                os.remove(temporaryPath)
            except OSError as e:
                log.warning(f"Failed to delete temporary file {temporaryPath}: {e}")
    
    return result_final

@router.get("/u/docs-analysis")
async def docsAnalysis():
    return await DocumentAnalysisController.pdf_local_analysis()

@router.get("/u/reports")
def viewReports():
    return ReportsController.get_reports()

@router.get("/u/docs")
async def viewDocs():
    return await DocumentController.viewAllDocs()

@router.get("/u/docs/{doc_id}")
async def view_doc_id(doc_id: int, background_tasks: BackgroundTasks):
    return await DocumentController.viewDocsById(doc_id, background_tasks)

@router.get("/u/cluster-events")
def getClusterEvents(k: int):
    return ClusterController.get_cluster_events(k)

# return all events
@router.get("/u/events")
def getAllEvents():
    return ClusterController.get_all_events()

@router.get("/u/memory-state")
def getMemoryState():
    return MemoryStateController.memoState()

@router.post("/u/rlhf/feedback")
async def submit_report_feedback(feedback: ReportFeedbackCreate):
    """
    Enviar feedback sobre um relatório C2M
    
    POST /v1/u/rlhf/feedback
    """
    return await RLHFController.submit_report_feedback(feedback)


@router.get("/u/rlhf/feedback/{feedback_id}")
async def get_feedback_endpoint(feedback_id: str):
    """
    Obter um feedback específico
    
    GET /v1/u/rlhf/feedback/{feedback_id}
    """
    return await RLHFController.get_feedback(feedback_id)


@router.get("/u/rlhf/reports/{report_id}/feedback-stats")
async def get_report_feedback_stats(report_id: str):
    """
    Obter estatísticas de feedback para um relatório
    
    GET /v1/u/rlhf/reports/{report_id}/feedback-stats
    """
    return await RLHFController.get_report_feedback_stats(report_id)


@router.get("/u/rlhf/adjustments")
async def get_adjustment_history(limit: int = 50):
    """
    Obter histórico de ajustes de peso
    
    GET /v1/u/rlhf/adjustments?limit=50
    """
    return await RLHFController.get_adjustment_history(limit)


@router.get("/u/rlhf/weights")
async def get_current_weights():
    """
    Obter pesos atuais do sistema C2M
    
    GET /v1/u/rlhf/weights
    """
    return await RLHFController.get_current_weights()


@router.post("/u/rlhf/process")
async def trigger_feedback_processing(min_feedbacks: int = 10):
    """
    Disparar processamento de feedback e ajuste de pesos (RLHF loop)
    
    POST /v1/u/rlhf/process?min_feedbacks=10
    """
    return await RLHFController.trigger_feedback_processing(min_feedbacks)


@router.post("/u/rlhf/reset-weights")
async def reset_weights():
    """
    Resetar pesos para valores padrão
    
    POST /v1/u/rlhf/reset-weights
    """
    return await RLHFController.reset_weights_to_defaults()