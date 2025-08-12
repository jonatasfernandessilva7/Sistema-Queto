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

from src.AiServices.services.AiAudioAnalysisService import (
    audioAnalysisDetectWordsInText,
    audioRecognize,
    extracting_characteristics
)
from src.backend.services.MicrophoneService import (
    recordMicrophoneAudio, 
    stopContinuousRecording
)

from langchain_core.messages import HumanMessage, AIMessage
# from src.backend.services.EmotionAnalysisService import emotionAnalysis
from src.agents.environment_organizational_agents.EmotionAgent import app as emotion_agent_app

from src.AiServices.services.AiAnswerService import (
    AiReactiveAnswer, 
    AiDeliberativePlanning
)
from src.AiServices.services.AiReportsService import (
    AiGeneretadReportsWithLlama, 
    AiSaveReports
)
from src.AiServices.AiMemory import (
    AiAddingEventHistory,
    AiCompareEventsHistory
)
from src.AiServices.AiApprenticeship import AiClassifyEvent
from src.AiServices.AiModels import EventModel

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

        emotionToString = "Error: could not analyze emotion"
        if textPresentsInAudio:
            agent_input_message  = HumanMessage(
                content=f"""Please analyze the emotion of the following audio transcript: '{textPresentsInAudio}'. 
                **After analysis, state the identified emotion and polarity clearly in your final response.**"""
            )
            initial_agent_state = {"messages": [agent_input_message]}
            print(initial_agent_state,"inicio estado\n")

            agent_response = None
            async for s in emotion_agent_app.astream(initial_agent_state):
                print(s, "s\n")
                if "llm" in s and s["llm"]["messages"]:
                    last_llm_message = s["llm"]["messages"][-1]
                    if isinstance(last_llm_message, AIMessage):
                        if not last_llm_message.tool_calls:
                            agent_response = last_llm_message.content
                            print(f"Final agent response captured: {agent_response}")
                            break
                elif "__end__" in s and s["__end__"]["messages"]:
                    final_messages = s["__end__"]["messages"]
                    print(final_messages)
                    if final_messages and isinstance(final_messages[-1], AIMessage):
                        print("no segundo if")
                        agent_response = final_messages[-1].content
                        print(agent_response)
                        break
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

        AiAddingEventHistory({"event": event.model_dump(), "timestamp": timestamp})

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
        similarMessage, similarEvent = AiCompareEventsHistory(event)

        aiReport = await AiGeneretadReportsWithLlama(event, aiReactiveAnswer, aiDeliberativePlann, priority)
        reportFile = AiSaveReports(aiReport, timestamp, priority)
        await sendEmailWithAttachments([reportFile, temporaryPath], os.getenv("DESTINATION_EMAIL"))

        return JSONResponse(
            content=
            {
            "status": 200,
            "correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis": correlation_between_spoken_text_and_phrases_that_may_signify_a_possible_cyber_crisis,
            "AI_reactive_answer": aiReactiveAnswer,
            "AI_deliberative_plan": aiDeliberativePlann,
            "priority": priority,
            "AI_report": aiReport,
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