from pathlib import Path

from fastapi import UploadFile, HTTPException, File, BackgroundTasks
from typing import List

from fastapi.responses import JSONResponse

from src.backend.services.service_documentos import salvar_arquivo, ver_todos_os_documentos, ver_documentos_por_id, \
    delete_document_service

PDF_FOLDER = Path("../uploads")

async def upload_file(file: List[UploadFile] = File(...) ):

    try:

        resultado = await salvar_arquivo(file)

        return JSONResponse(content={ "status":200, "arquivos": resultado})
    
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))
    
def ver_todos_documentos():

    try: 

        resultado = ver_todos_os_documentos()

        if not resultado:

            return False

        return resultado
    
    except Exception as e:

        return e

def ver_documento_pelo_id(doc_id: int, background_tasks: BackgroundTasks):
    """
    Controller function to view a document by ID.
    Delegates to the service layer.
    """
    # Pass background_tasks to the service function for file cleanup
    doc_response = ver_documentos_por_id(doc_id, background_tasks)

    if not doc_response:
        raise HTTPException(status_code=404, detail="Documento não encontrado ou erro ao processar.")

    return doc_response

def delete_document_controller(doc_id: int):
    """
    API endpoint to delete a document by its ID.
    """
    result = delete_document_service(doc_id)

    # Check the return type from service.py for detailed handling
    if isinstance(result, tuple): # If the service returned (message, status_code)
        message, status_code = result
        raise HTTPException(status_code=status_code, detail=message["message"])
    else: # If the service returned just the success message dictionary
        return result
