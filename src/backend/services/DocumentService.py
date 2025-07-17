import os
import uuid
import aiofiles

from fastapi import UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Dict
from src.backend.repository.GenericsRepository import add_documentos, get_all_documentos, get_documentos_by_id, delete_document_by_id

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def saveDocumentsCompany(files: List[UploadFile] = File(...)) -> List[Dict]:

    try:
        uploaded_files_info = []

        for file in files:
            file_location = os.path.join(UPLOAD_DIR, file.filename)
            files_size = 0
            
            async with aiofiles.open(file_location, "wb") as buffer:
                while content := await file.read(1024 * 1024):
                    await buffer.write(content)
                    files_size += len(content)

            try:
                add_documentos(file.filename, file_location)
                uploaded_files_info.append({"filename": file.filename, "status": "Arquivo enviado com sucesso."})

            except Exception as e:
                return [{"filename": file.filename, "error": e}]
            
    except Exception as e:
        return e
    return uploaded_files_info

def viewAllCompanyDocuments():

    documents = get_all_documentos()

    try :
        if not documents:
            return False
        return documents
    
    except Exception as e:
        return e

def viewAllCompanyDocumentsById(doc_id: int, background_tasks: BackgroundTasks):
    """
    Retrieves document content from DB, saves it temporarily, and prepares FileResponse.

    Args:
        doc_id: The ID of the document to view.
        background_tasks: FastAPI's BackgroundTasks for cleanup.

    Returns:
        FileResponse if successful, None otherwise.
    """
    # Get filename and binary content from the database
    filename_from_db, pdfContent = get_documentos_by_id(doc_id)

    if not pdfContent:
        return None

    temp_filename = f"{uuid.uuid4()}_{filename_from_db}"
    temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)

    try:
        with open(temp_filepath, 'wb') as f:
            f.write(pdfContent)
        background_tasks.add_task(os.remove, temp_filepath)

        return FileResponse(
            path=temp_filepath,
            media_type="application/pdf",
            filename=filename_from_db,
            headers={"Content-Disposition": f'inline; filename="{filename_from_db}"'}
        )
    except Exception as e:
        print(f"Error in document process (ID: {doc_id}): {e}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return None

def delete_document_service(doc_id: int):
    """
    Handles the deletion of a document, including database record and potential temporary files.

    Args:
        doc_id: The ID of the document to delete.

    Returns:
        A dictionary indicating success or failure.
    """
    try:
        deleted = delete_document_by_id(doc_id)
        if deleted:
            return {"message": f"Document with id {doc_id} deleted."}
        else:
            return {"message": f"Document with id {doc_id} not found or not deleted."}, 404

    except Exception as e:
        print(f"Error in delete document id (ID: {doc_id}): {e}")
        return {"message": "Internal error."}, 500
