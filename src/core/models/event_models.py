"""
Core domain models used across the application.
These models are centralized to avoid duplication and circular imports.
"""

from pydantic import BaseModel
from typing import Dict


class EventModel(BaseModel):
    """
    Represents a crisis/security event in the system.
    
    Attributes:
        type: The type of event (e.g., 'breach', 'attack', 'anomaly')
        origin: The source or origin of the event
        details: A dictionary containing detailed event information
    """
    type: str
    origin: str
    details: Dict[str, str]


class FeedbackModel(BaseModel):
    """
    Represents human feedback on AI classifications.
    
    Attributes:
        event_id: Reference to the event being classified
        llm_classification: The AI's original classification
        llm_priority: The AI's original priority assessment
        human_classification: The human's corrected classification
        human_priority: The human's corrected priority assessment
        comment: Optional comment from the human reviewer
    """
    event_id: int
    llm_classification: str
    llm_priority: str
    human_classification: str
    human_priority: str
    comment: str | None = None
