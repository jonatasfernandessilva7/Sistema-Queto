"""
Audio Analysis Services - consolidated audio processing services.
"""

from src.AiServices.services.AiAudioAnalysisService import (
    audioAnalysisDetectWordsInText,
    audioRecognize,
    extracting_characteristics
)
from src.backend.services.MicrophoneService import (
    recordMicrophoneAudio,
    stopContinuousRecording
)

__all__ = [
    # Audio analysis
    'audioAnalysisDetectWordsInText',
    'audioRecognize',
    'extracting_characteristics',
    # Microphone services
    'recordMicrophoneAudio',
    'stopContinuousRecording',
]
