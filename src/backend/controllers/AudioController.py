import datetime
import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from scipy.io import wavfile
from dotenv import load_dotenv

from src.core.utils import idempotency
from src.core.utils import sendEmailWithAttachments

from src.api.services.audio import (
    audioAnalysisDetectWordsInText,
    audioRecognize,
    extracting_characteristics,
    recordMicrophoneAudio,
    stopContinuousRecording
)

from langchain_core.messages import HumanMessage, AIMessage
#from src.agents.environment_organizational_agents_tools.EmotionAgent import app as emotion_agent_app
from src.agents.environment_organizational_agent import outers_agent

from src.api.services.analysis import (
    AiReactiveAnswer, 
    AiDeliberativePlanning,
    AiClassifyEvent
)
from src.api.services.reports import (
    AiSaveReports
)
from src.AiServices.services.AiReportsService import AiGenerateReportC2M
from src.core.models import (
    EventModel,
    add_event_to_history,
    compare_events_with_history
)

load_dotenv()

# emotion = None

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

        eventDetails = {
            "audio_path": temporaryPath,
            "time_in_seconds": str(len(signal) / rate),
            "sample_rate": str(rate)
        }

        num_voices = extracting_characteristics(temporaryPath)
        eventDetails['num_voices'] = str(num_voices)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Gerar timestamp aqui

        textPresentsInAudio = audioRecognize(temporaryPath)
        print(textPresentsInAudio)

        correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis = audioAnalysisDetectWordsInText(textPresentsInAudio)
        eventDetails["correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis"] = correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis
        agent_response = None
        emotionToString = "Error: could not analyze emotion"
        if textPresentsInAudio:
            agent_response = await outers_agent.arun(
                f"Analise a emoção do seguinte texto e me retorne a emoção e polaridade identificadas: '{textPresentsInAudio}'"
            )
            emotionToString = agent_response
        print("cheguei aqui\n")

        if agent_response:
            emotionToString = agent_response
        else:
            emotionToString = "Agent did not provide an emotion analysis result."

        eventDetails['emotion'] = emotionToString
        eventDetails['text_presents_in_audio'] = textPresentsInAudio
        eventDetectedType = await AiClassifyEvent(eventDetails)

        event = EventModel(
            type=eventDetectedType,
            origin="microphone_local",
            details=eventDetails
        )

        add_event_to_history({"event": event.model_dump(), "timestamp": timestamp})

        if "não encontrei nenhuma correspondencia" in correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis:
            return JSONResponse({
                "status": 200,
                "message": "sem crises detectadas",
                "emotion": emotionToString,
                "num_voices": str(num_voices)
            })

        aiReactiveAnswer = AiReactiveAnswer(event)
        aiDeliberativePlann = AiDeliberativePlanning(event)
        priority = await AiClassifyEvent(event)
        similarMessage, similarEvent = compare_events_with_history(event)

        c2m_analysis = await AiGenerateReportC2M(event)
        aiReport = c2m_analysis.get('analysis_summary', 'Relatório C2M gerado')
        reportFile = AiSaveReports(aiReport, timestamp, priority)
        await sendEmailWithAttachments([reportFile, temporaryPath], os.getenv("DESTINATION_EMAIL"))

        return JSONResponse(
            content=
            {
            "status": 200,
            "message": "crise detectada, enviando email",
            "correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis": correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis,
            "AI_reactive_answer": aiReactiveAnswer,
            "AI_deliberative_plan": aiDeliberativePlann,
            "priority": priority,
            "AI_report": aiReport,
            "c2m_probability": c2m_analysis.get('probability_pct', 0),
            "c2m_priority": c2m_analysis.get('priority', 'Desconhecido'),
            "similarity": similarMessage,
            "similar_event": similarEvent,
            "emotion": emotionToString,
            "num_voices": str(num_voices)
            }
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="audio file not found after recording.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in audio process: {e}")

def sync_audio_processing(audio_path):
    """Processamento de áudio em CPU (síncrono)."""
    rate, signal = wavfile.read(audio_path)
    if len(signal.shape) > 1:
        signal = signal[:, 0]

    num_voices = extracting_characteristics(audio_path)

    return {
        "rate": rate,
        "signal": signal,
        "num_voices": num_voices
    }    

async def receivesAndProcessAudioUploaded(audio_path, q=None):
    try:
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            if q:
                await q.put(HTTPException(status_code=500, detail="Audio file not found or is empty."))
            return

        print("Arquivo salvo em:", audio_path)

        loop = asyncio.get_running_loop()
        audio_data = await loop.run_in_executor(None, lambda: sync_audio_processing(audio_path))

        rate = audio_data["rate"]
        signal = audio_data["signal"]
        num_voices = audio_data["num_voices"]

        print("Taxa de amostragem:", rate)

        eventDetails = {
            "audio_path": audio_path,
            "time_in_seconds": str(len(signal) / rate),
            "sample_rate": str(rate),
            "num_voices": str(num_voices)
        }
        
        textPresentsInAudio = audioRecognize(audio_path)
        print("Texto reconhecido:", textPresentsInAudio)
        
        emotionToString = "Error: could not analyze emotion"
        if textPresentsInAudio:
            agent_response = await outers_agent.arun(
                f"Analise a emoção do seguinte texto e me retorne a emoção e polaridade identificadas: '{textPresentsInAudio}'"
            )
            emotionToString = agent_response or "Agent did not provide an emotion analysis result."

        eventDetails['emotion'] = emotionToString
        eventDetails['text_presents_in_audio'] = textPresentsInAudio
        eventDetectedType = await AiClassifyEvent(eventDetails)

        correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis = audioAnalysisDetectWordsInText(textPresentsInAudio)
        eventDetails["correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis"] = correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis

        event = EventModel(
            type=eventDetectedType,
            origin="microphone_local",
            details=eventDetails
        )

        add_event_to_history({"event": event.model_dump(), "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")})

        if "não encontrei nenhuma correspondencia" in correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis:
            result = JSONResponse({
                "status": 200,
                "message": "sem crises detectadas",
                "emotion": emotionToString,
                "num_voices": str(num_voices)
            })
            if q:
                await q.put(result)
            return

        aiReactiveAnswer = AiReactiveAnswer(event)
        aiDeliberativePlann = AiDeliberativePlanning(event)
        type_event = await AiClassifyEvent(event)
        similarMessage, similarEvent = compare_events_with_history(event)

        c2m_analysis = await AiGenerateReportC2M(event)
        aiReport = c2m_analysis.get('analysis_summary', 'Relatório C2M gerado')
        reportFile = AiSaveReports(aiReport, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), type_event)
        await sendEmailWithAttachments([reportFile, audio_path], os.getenv("DESTINATION_EMAIL"))

        result = JSONResponse(
            content={
                "status": 200,
                "message": "crise detectada, enviando email",
                "correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crise": correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis,
                "AI_reactive_answer": aiReactiveAnswer,
                "AI_deliberative_plan": aiDeliberativePlann,
                "type_event": type_event,
                "AI_report": aiReport,
                "c2m_probability": c2m_analysis.get('probability_pct', 0),
                "c2m_priority": c2m_analysis.get('priority', 'Desconhecido'),
                "similarity": similarMessage,
                "similar_event": similarEvent,
                "emotion": emotionToString,
                "num_voices": str(num_voices)
            }
        )
        if q:
            await q.put(result)
        return

    except Exception as e:
        print(f"Erro detalhado: {e}")
        if q:
            await q.put(HTTPException(status_code=500, detail=f"Error in audio process: {e}"))
        return