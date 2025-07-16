import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import List
from src.backend.controllers import (
    controller_documentos,
    controller_estado,
    controller_cluster,
    controller_evento_texto,
    controller_feedback,
    controller_analise_de_documentos,
    controller_relatorios
)
from src.IA.modelos import Evento
from src.IA.services.feedback import Feedback
from src.backend.controllers.controller_audio import iniciarGravacao, receber_e_processar_audio

router = APIRouter(
    prefix="/v1"
)

@router.delete("/documentos/{doc_id}")
def delete_doc_id(doc_id):
    return controller_documentos.delete_document_controller(doc_id)

@router.post("/feedback")
async def human_feedback(feedback: Feedback):
    return await controller_feedback.submit_feedback(feedback)

@router.post("/upload")
async def upload_file(file: List[UploadFile] = File(...)):
    return await controller_documentos.upload_file(file)

@router.post("/evento-texto")
async def receber_evento(evento: Evento):
    return await controller_evento_texto.receber_evento(evento)

@router.post("/iniciar-gravacao")
async def receber_audio():
    request_idempotency_key = str(uuid.uuid4())
    return await iniciarGravacao(idempotency_key=request_idempotency_key)

@router.post("/parar-gravacao")
async def parar_gravacao():
    return await receber_e_processar_audio()

@router.get("/analise-documentos")
async def analise_de_documentos():
    return await controller_analise_de_documentos.analisar_pdf_local()

@router.get("/ver-relatorios")
def ver_relatorios():
    return controller_relatorios.get_relatorios()

@router.get("/documentos")
def ver_documentos():
    return controller_documentos.ver_todos_documentos()

@router.get("/documentos/{doc_id}")
def view_doc_id(doc_id: int, background_tasks: BackgroundTasks):
    return controller_documentos.ver_documento_pelo_id(doc_id, background_tasks)

@router.get("/eventos-clusterizados")
def eventos_clusterizados(k: int):
    return controller_cluster.eventos_clusterizados(k)

@router.get("/estado-memoria")
def obter_estado():
    return controller_estado.obter_estado()