import os
import uuid

import aiofiles
from fastapi import UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Dict
from src.backend.db.db import add_documentos, get_all_documentos, get_documentos_by_id, delete_document_by_id

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def salvar_arquivo(files: List[UploadFile] = File(...)) -> List[Dict]:

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

def ver_todos_os_documentos():

    documentos = get_all_documentos()

    try : 

        if not documentos:

            return False

        return documentos
    
    except Exception as e:

        return e

def ver_documentos_por_id(doc_id: int, background_tasks: BackgroundTasks):
    """
    Retrieves document content from DB, saves it temporarily, and prepares FileResponse.

    Args:
        doc_id: The ID of the document to view.
        background_tasks: FastAPI's BackgroundTasks for cleanup.

    Returns:
        FileResponse if successful, None otherwise.
    """
    # Get filename and binary content from the database
    filename_from_db, conteudo_pdf = get_documentos_by_id(doc_id)

    if not conteudo_pdf:
        # Document not found in DB or content is empty
        return None

    # Create a unique temporary file path to save the PDF content.
    # This is essential because FileResponse needs a path to an actual file.
    temp_filename = f"{uuid.uuid4()}_{filename_from_db}"
    temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)

    try:
        # Write the binary content to the temporary file
        with open(temp_filepath, 'wb') as f:
            f.write(conteudo_pdf)

        # Schedule cleanup: Add a background task to delete the temporary file
        # after the FileResponse has been sent to the client. This is vital
        # to prevent your server's disk from filling up.
        background_tasks.add_task(os.remove, temp_filepath)

        # Return a FileResponse, pointing to the temporary file but using the original filename for download
        return FileResponse(
            path=temp_filepath,
            media_type="application/pdf",
            filename=filename_from_db, # This is the name the user will see for download
            headers={"Content-Disposition": f'inline; filename="{filename_from_db}"'} # Use 'inline' to display in browser
        )
    except Exception as e:
        print(f"Erro ao processar e servir o documento (ID: {doc_id}): {e}")
        # If an error occurs during writing, try to clean up the partially created file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return None # Indicate failure

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
            return {"message": f"Documento com ID {doc_id} deletado com sucesso."}
        else:
            return {"message": f"Documento com ID {doc_id} não encontrado ou não pôde ser deletado."}, 404
    except Exception as e:
        print(f"Erro no serviço de deleção do documento (ID: {doc_id}): {e}")
        return {"message": "Erro interno ao tentar deletar o documento."}, 500
