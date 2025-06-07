import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import HTTPException
from src.IA.memoria import (
    clusterizar_eventos,
    obter_historico_eventos
)

def eventos_clusterizados(k: int = 3):

    historico = obter_historico_eventos()

    try:

        return clusterizar_eventos(historico, k)
    
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=str(e))