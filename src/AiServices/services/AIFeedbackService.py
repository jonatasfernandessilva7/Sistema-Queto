from pydantic import BaseModel
from typing import Optional

class Feedback(BaseModel):
    
    event_id: Optional[int] = None
    human_classification: str 
    human_priority: str
    comment: str = None