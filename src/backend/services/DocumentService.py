"""
Gerencia upload, listagem e remoção de documentos corporativos.
Após upload bem-sucedido, invalida o cache de embeddings do VectorSearchService
para que o próximo cálculo de conformidade reflita os novos documentos.
"""

from __future__ import annotations

import logging
import os
import uuid

import aiofiles
from fastapi import BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, List, Optional

from src.backend.repository.GenericsRepository import (
    add_documentos,
    delete_document_by_id,
    get_all_documentos,
    get_documentos_by_id,
)
from src.backend.services.VectorSearchService import invalidate_document_cache

log = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def saveDocumentsCompany(files: List[UploadFile] = File(...)) -> List[Dict]:
    """
    Salva arquivos no diretório de uploads e registra no banco.
    Invalida o cache de embeddings do VectorSearchService após cada upload.
    """
    uploaded: List[Dict] = []

    for file in files:
        dest = UPLOAD_DIR / (file.filename or f"doc_{uuid.uuid4()}")
        file_size = 0

        try:
            async with aiofiles.open(dest, "wb") as buf:
                while chunk := await file.read(1024 * 1024):
                    await buf.write(chunk)
                    file_size += len(chunk)

            add_documentos(file.filename, str(dest))

            # Invalidar cache: próxima conformidade recalculará embeddings
            invalidate_document_cache()

            log.info("Documento salvo: %s (%d bytes)", file.filename, file_size)
            uploaded.append({"filename": file.filename, "status": "enviado com sucesso"})

        except Exception as exc:
            log.error("Erro ao salvar %s: %s", file.filename, exc)
            uploaded.append({"filename": file.filename, "error": str(exc)})

    return uploaded

async def viewAllCompanyDocuments():
    """Lista todos os documentos persistidos."""
    try:
        docs = await get_all_documentos()
        return docs if docs else False
    except Exception as exc:
        log.error("Erro ao listar documentos: %s", exc)
        return exc

async def viewAllCompanyDocumentsById(doc_id: int, background_tasks: BackgroundTasks):
    """Recupera e retorna um documento pelo ID como FileResponse."""
    filename, pdf_bytes = await get_documentos_by_id(doc_id)
    if not pdf_bytes:
        return None

    temp_name = f"{uuid.uuid4()}_{filename}"
    temp_path = UPLOAD_DIR / temp_name

    try:
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)
        background_tasks.add_task(_remove_file, temp_path)
        return FileResponse(
            path=str(temp_path),
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except Exception as exc:
        log.error("Erro ao servir doc_id=%d: %s", doc_id, exc)
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return None

def delete_document_service(doc_id: int):
    """Remove documento do banco e do cache de embeddings."""
    try:
        deleted = delete_document_by_id(doc_id)
        if deleted:
            invalidate_document_cache(doc_id)
            return {"message": f"Documento {doc_id} removido."}
        return {"message": f"Documento {doc_id} não encontrado."}, 404
    except Exception as exc:
        log.error("Erro ao remover doc_id=%d: %s", doc_id, exc)
        return {"message": "Erro interno."}, 500

def _remove_file(path: Path) -> None:
    """Remove arquivo temporário — usado em BackgroundTasks."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        log.warning("Não foi possível remover %s: %s", path, exc)
