from fastapi import UploadFile, File, HTTPException
from src.backend.services.service_upload_arquivo import salvar_arquivo

async def upload_file(file: UploadFile = File(...)):

    try: 

        resultado = await salvar_arquivo(file)
        return resultado
    
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=str(e))
