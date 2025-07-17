import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from scipy.io import wavfile
from dotenv import load_dotenv

from src.backend.utils.idenpotenceFuncionUtils import idempotency
from src.backend.utils.EmailUtils import sendEmailWithAttachments

from src.backend.services.AudioAnalysisService import (
    audioAnalysisWithFft,
    audioAnalysisLowPassFilter,
    audioAnalysisDetectPatterns,
    saveSpectogram
)
from src.backend.services.MicrophoneService import (
    recordMicrophoneAudio, 
    audioRecognize, 
    stopContinuousRecording
)
from src.backend.services.EmotionAnalysisService import emotionAnalysis

from src.IA.services.AiAnswerService import (
    AiReactiveAnswer, 
    AiDeliberativePlanning
)
from src.IA.services.AiReportsService import (
    AiGeneretadReportsWithLlama, 
    AiSaveReports
)
from src.IA.AiMemory import (
    AiAddingEventHistory,
    AiCompareEventsHistory
)
from src.IA.AiApprenticeship import AiClassifyEvent
from src.IA.AiModels import EventModel

load_dotenv()

emotion = None

@idempotency
async def startAudioMeeting(**kwargs):
    recordingMeeting = recordMicrophoneAudio()

    if recordingMeeting is None:
        raise HTTPException(status_code=404, detail="Audio file is null.")

    return recordingMeeting

async def receivesAndProcessAudio():

    temporaryPath = stopContinuousRecording()

    if "No recording" in temporaryPath or "Error" in temporaryPath:
        raise HTTPException(status_code=400, detail=temporaryPath)

    try:
        if not os.path.exists(temporaryPath) or os.path.getsize(temporaryPath) == 0:
            raise HTTPException(status_code=500, detail="Generated audio file is empty or does not exist.")

        rate, signal = wavfile.read(temporaryPath)
        if len(signal.shape) > 1:
            signal = signal[:, 0]
        analysisResult = audioAnalysisWithFft(temporaryPath)

        eventDetails = {
            "audio_path": temporaryPath,
            "time_in_seconds": str(len(signal) / rate),
            "sample_rate": str(rate)
        }

        if "peak_frequency" in analysisResult and "peak_amplitude" in analysisResult:
            eventDetails["peak_frequency"] = str(analysisResult["peak_frequency"])
            eventDetails["peak_amplitude"] = str(analysisResult["peak_amplitude"])
            eventDetails["status"] = analysisResult.get("status", "desconhecido")
        elif "erro" in analysisResult:
            eventDetails["error_audio_analysis"] = analysisResult["error"]

        signal_filtrado = audioAnalysisLowPassFilter(signal, rate)
        pattern = audioAnalysisDetectPatterns(signal_filtrado, rate)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Gerar timestamp aqui
        spectrogramPath = saveSpectogram(signal, rate, timestamp)

        eventDetails["detected_pattern"] = pattern
        eventDetails["spectrogram_path"] = spectrogramPath

        textPresentsInAudio = audioRecognize(temporaryPath)
        print(textPresentsInAudio)

        emotionAnalysisResult = emotionAnalysis(textPresentsInAudio)
        if "error" in emotionAnalysisResult:
            emotionToString = f"Error: {emotionAnalysisResult['error']}"
        else:
            emotionToString = f"{emotionAnalysisResult['emotion']} (polarity={emotionAnalysisResult['polarity']:.2f})"

        eventDetails["emotion"] = emotionToString
        eventDetails["text_presents_in_audio"] = textPresentsInAudio
        EventDetectedTipy = await AiClassifyEvent(eventDetails)

        event = EventModel(
            type=EventDetectedTipy,
            origin="microphone_local",
            details=eventDetails
        )

        AiAddingEventHistory({"event": event.model_dump(), "timestamp": timestamp})

        aiReactiveAnswer = AiReactiveAnswer(event)
        aiDeliberativePlann = AiDeliberativePlanning(event)
        priority = await AiClassifyEvent(event)
        similarMessage, similarEvent = AiCompareEventsHistory(event)

        aiReport = await AiGeneretadReportsWithLlama(event, aiReactiveAnswer, aiDeliberativePlann, priority)
        reportFile = AiSaveReports(aiReport, timestamp, priority)
        await sendEmailWithAttachments([reportFile, temporaryPath], os.getenv("DESTINATION_EMAIL"))

        return JSONResponse(
            content=
            {
            "status": 200,
            "detected_pattern": pattern,
            "AI_reactive_answer": aiReactiveAnswer,
            "AI_deliberative_plan": aiDeliberativePlann,
            "priority": priority,
            "AI_report": aiReport,
            "similarity": similarMessage,
            "similar_event": similarEvent,
            "spectrogram": spectrogramPath,
            "emotion": emotion
            }
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="audio file not found after recording.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in audio process: {e}")