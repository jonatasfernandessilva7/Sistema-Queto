from pydantic import BaseModel
from typing import Dict

class Evento(BaseModel):
    
    tipo: str
    origem: str
    detalhes: Dict[str, str]