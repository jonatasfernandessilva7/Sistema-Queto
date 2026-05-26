import os
import sys

from fastapi.responses import JSONResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

from fastapi import HTTPException
from src.core.models import cluster_events, get_event_history_data

def get_cluster_events(k: int = 3):

    history = get_event_history_data()

    try:
        cluster = cluster_events(history, k)
        return JSONResponse(content={"status":200, "events": cluster})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_all_events():
    history = get_event_history_data()
    try:
        return JSONResponse(content={"status":200, "events": history})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))