from pathlib import Path
from fastapi import UploadFile, HTTPException, File, BackgroundTasks
from typing import List
from fastapi.responses import JSONResponse

from src.backend.services.DocumentService import (
    saveDocumentsCompany,
    viewAllCompanyDocuments,
    viewAllCompanyDocumentsById,
    delete_document_service
)

PDF_FOLDER = Path("../uploads")

async def upload_file(file: List[UploadFile] = File(...) ):

    try:
        result = await saveDocumentsCompany(file)
        return JSONResponse(content={ "status":200, "files": result})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def viewAllDocs():

    try:
        result = viewAllCompanyDocuments()
        if not result:
            return False
        return result

    except Exception as e:
        return e

def viewDocsById(doc_id: int, background_tasks: BackgroundTasks):

    doc_response = viewAllCompanyDocumentsById(doc_id, background_tasks)
    if not doc_response:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc_response

def delete_document_controller(doc_id: int):

    result = delete_document_service(doc_id)
    if isinstance(result, tuple):
        message, status_code = result
        raise HTTPException(status_code=status_code, detail=message["message"])
    else:
        return result
