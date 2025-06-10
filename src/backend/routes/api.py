import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import APIRouter, UploadFile, File
from typing import List
from src.backend.controllers import (
    controller_estado,
    controller_audio,
    controller_cluster,
    controller_evento_texto,
    controller_upload,
    controller_feedback
)
from src.IA.modelos import Evento
from src.IA.services.feedback import Feedback

router = APIRouter(
    prefix="/v1"
)

@router.post("/feedback")
async def human_feedback(feedback: Feedback):
    return await controller_feedback.submit_feedback(feedback)

@router.post("/upload")
async def upload_file(file: List[UploadFile] = File(...)):
    return await controller_upload.upload_file(file)

@router.post("/evento-texto")
async def receber_evento(evento: Evento):
    return await controller_evento_texto.receber_evento(evento)

@router.post("/evento-audio")
async def receber_audio():
    return await controller_audio.receber_audio()

@router.get("/eventos-clusterizados")
def eventos_clusterizados(k: int):
    return controller_cluster.eventos_clusterizados(k)

@router.get("/estado-memoria")
def obter_estado():
    return controller_estado.obter_estado()