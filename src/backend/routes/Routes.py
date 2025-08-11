import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import List

from src.backend.controllers import (
    DocumentController,
    MemoryStateController,
    ClusterController,
    TextEventController,
    FeedbackController,
    DocumentAnalysisController,
    ReportsController
)

from src.AiServices.AiModels import EventModel
from src.AiServices.services.AIFeedbackService import Feedback
from src.backend.controllers.AudioController import startAudioMeeting, receivesAndProcessAudio

router = APIRouter(
    prefix="/v1"
)

@router.delete("/u/docs/{doc_id}")
def delete_doc_id(doc_id):
    return DocumentController.delete_document_controller(doc_id)

@router.post("/u/feedback")
async def human_feedback(feedback: Feedback):
    return await FeedbackController.submit_feedback(feedback)

@router.post("/u/upload")
async def upload_file(file: List[UploadFile] = File(...)):
    return await DocumentController.upload_file(file)

@router.post("/u/evento-texto")
async def receivesEvent(evento: EventModel):
    return await TextEventController.receiveEvent(evento)

@router.post("/u/start-recording")
async def receivesAudioMeeting():
    request_idempotency_key = str(uuid.uuid4())
    return await startAudioMeeting(idempotency_key=request_idempotency_key)

@router.post("/u/stop-recording")
async def stopAudioMeeting():
    return await receivesAndProcessAudio()

@router.get("/u/docs-analysis")
async def docsAnalysis():
    return await DocumentAnalysisController.pdf_local_analysis()

@router.get("/u/reports")
def viewReports():
    return ReportsController.get_reports()

@router.get("/u/docs")
def viewDocs():
    return DocumentController.viewAllDocs()

@router.get("/u/docs/{doc_id}")
def view_doc_id(doc_id: int, background_tasks: BackgroundTasks):
    return DocumentController.viewDocsById(doc_id, background_tasks)

@router.get("/u/cluster-events")
def getClusterEvents(k: int):
    return ClusterController.get_cluster_events(k)

@router.get("/u/memory-state")
def getMemoryState():
    return MemoryStateController.memoState()