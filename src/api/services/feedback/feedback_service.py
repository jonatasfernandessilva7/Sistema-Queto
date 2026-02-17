"""
Feedback Services - consolidated feedback handling.
"""

from src.backend.services.FeedbackService import service_submit_feedback
from src.AiServices.services.AIFeedbackService import Feedback

__all__ = [
    'service_submit_feedback',
    'Feedback',
]
