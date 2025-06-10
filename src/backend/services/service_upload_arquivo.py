import os
import aiofiles 

from fastapi import UploadFile, File
from typing import List, Dict
from src.backend.db.db import add_documentos

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

                return e
            
    except Exception as e:

        return e

    return uploaded_files_info