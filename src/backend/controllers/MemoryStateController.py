import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.IA.AiMemory import (
    obter_estado_memoria,
)
def memoState():
    
    try: 
        estado = obter_estado_memoria()
        return JSONResponse(content={"status":200, "estado": estado})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    