import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import HTTPException
from src.IA.memoria import (
    obter_estado_memoria,
)
def obter_estado():
    
    try: 

        return obter_estado_memoria()
    
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=str(e))
    
    