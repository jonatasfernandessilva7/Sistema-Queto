import os
import sys

from fastapi.responses import JSONResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import HTTPException
from src.AiServices.AiMemory import (
    clusterEvents,
    getEventHistory
)

def get_cluster_events(k: int = 3):

    history = getEventHistory()

    try:
        cluster = clusterEvents(history, k)
        return JSONResponse(content={"status":200, "events": cluster})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))