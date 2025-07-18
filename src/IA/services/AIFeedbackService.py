from pydantic import BaseModel

class Feedback(BaseModel):
    
    event_id: int 
    human_classification: str 
    human_priority: str
    comment: str = None