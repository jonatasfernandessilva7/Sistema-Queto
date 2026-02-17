import os
import uuid
import aiofiles
import logging

from fastapi import UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
from src.backend.repository.GenericsRepository import add_documentos, get_all_documentos, get_documentos_by_id, delete_document_by_id
from src.core.config.settings import Settings

log = logging.getLogger(__name__)

# Use centralized settings for upload directory
UPLOAD_DIR = Settings.UPLOADS_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def saveDocumentsCompany(files: List[UploadFile] = File(...)) -> List[Dict]:
    """
    Save uploaded documents to the file system and database.
    
    Args:
        files: List of files to upload
        
    Returns:
        List of dictionaries with upload status or error details
    """
    try:
        uploaded_files_info = []

        for file in files:
            if not file.filename:
                log.warning("File with no filename received")
                uploaded_files_info.append({"error": "File must have a valid filename"})
                continue
                
            try:
                file_location = str(UPLOAD_DIR / file.filename)
                files_size = 0
                
                async with aiofiles.open(file_location, "wb") as buffer:
                    while content := await file.read(1024 * 1024):
                        await buffer.write(content)
                        files_size += len(content)

                add_documentos(file.filename, file_location)
                log.info(f"File {file.filename} uploaded successfully ({files_size} bytes)")
                uploaded_files_info.append({
                    "filename": file.filename, 
                    "status": "Arquivo enviado com sucesso.",
                    "size": files_size
                })

            except IOError as e:
                log.error(f"IO error uploading file {file.filename}: {e}")
                uploaded_files_info.append({
                    "filename": file.filename, 
                    "error": f"IO error: {str(e)}"
                })
            except Exception as e:
                log.error(f"Unexpected error uploading file {file.filename}: {e}")
                uploaded_files_info.append({
                    "filename": file.filename, 
                    "error": f"Upload failed: {str(e)}"
                })
            
    except Exception as e:
        log.error(f"Fatal error in saveDocumentsCompany: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing uploads")
        
    return uploaded_files_info

async def viewAllCompanyDocuments():
    """
    Retrieve all documents from the database.
    
    Returns:
        List of documents or empty list if none found
    """
    try:
        documents = await get_all_documentos()
        if not documents:
            log.info("No documents found in database")
            return []
        log.info(f"Retrieved {len(documents)} documents")
        return documents
    
    except Exception as e:
        log.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents from database")

async def viewAllCompanyDocumentsById(doc_id: int, background_tasks: BackgroundTasks):
    """
    Retrieve document content from DB, save it temporarily, and prepare FileResponse.

    Args:
        doc_id: The ID of the document to view.
        background_tasks: FastAPI's BackgroundTasks for cleanup.

    Returns:
        FileResponse if successful, HTTPException otherwise.
    """
    try:
        # Get filename and binary content from the database
        filename_from_db, pdfContent = await get_documentos_by_id(doc_id)

        if not pdfContent or not filename_from_db:
            log.warning(f"Document {doc_id} not found or has no content")
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        temp_filename = f"{uuid.uuid4()}_{filename_from_db}"
        temp_filepath = str(UPLOAD_DIR / temp_filename)

        with open(temp_filepath, 'wb') as f:
            f.write(pdfContent)
        
        background_tasks.add_task(os.remove, temp_filepath)
        log.info(f"Serving document {doc_id} as {filename_from_db}")

        return FileResponse(
            path=temp_filepath,
            media_type="application/pdf",
            filename=filename_from_db,
            headers={"Content-Disposition": f'inline; filename="{filename_from_db}"'}
        )
        
    except HTTPException:
        raise
    except IOError as e:
        log.error(f"IO error retrieving document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Error reading document file")
    except Exception as e:
        log.error(f"Unexpected error retrieving document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal error processing document")

def delete_document_service(doc_id: int):
    """
    Handles the deletion of a document, including database record and potential temporary files.

    Args:
        doc_id: The ID of the document to delete.

    Returns:
        Tuple of (dict with result, HTTP status code)
    """
    try:
        deleted = delete_document_by_id(doc_id)
        if deleted:
            log.info(f"Document {doc_id} deleted successfully")
            return {"message": f"Document with id {doc_id} deleted."}, 200
        else:
            log.warning(f"Document {doc_id} not found during deletion")
            return {"message": f"Document with id {doc_id} not found or not deleted."}, 404

    except Exception as e:
        log.error(f"Error deleting document {doc_id}: {e}")
        return {"message": "Internal error while deleting document."}, 500
