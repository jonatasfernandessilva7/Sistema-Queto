import os
import aiofiles 

from fastapi import UploadFile, File
from typing import List

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def salvar_arquivo(files: List[UploadFile] = File(...)): 
    uploaded_files_info = []

    for file in files:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        
        async with aiofiles.open(file_location, "wb") as buffer:
            while content := await file.read(1024): 
                await buffer.write(content)
        
        uploaded_files_info.append({"filename": file.filename, "status": "Arquivo enviado com sucesso."})

    return uploaded_files_info