from fastapi import UploadFile, HTTPException, File
from typing import List
from src.backend.services.service_documentos import salvar_arquivo, ver_todos_os_documentos

async def upload_file(file: List[UploadFile] = File(...) ):

    try:

        resultado = await salvar_arquivo(file)

        return resultado
    
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
