import os
import aiofiles 

from fastapi import UploadFile

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def salvar_arquivo(file: UploadFile): 

    file_location = os.path.join(UPLOAD_DIR, file.filename)

    async with aiofiles.open(file_location, "wb") as buffer:
        
        while content := await file.read(1024): 
            await buffer.write(content)

    return {"filename": file.filename, "status": "Arquivo enviado com sucesso."}