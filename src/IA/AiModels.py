from pydantic import BaseModel
from typing import Dict

class EventModel(BaseModel):
    
    type: str
    origin: str
    details: Dict[str, str]