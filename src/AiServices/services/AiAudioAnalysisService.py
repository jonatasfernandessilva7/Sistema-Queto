import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)
phrases_crisis = "data_phrases_relationship_with_cyber_crisis/data.txt"

def audioAnalysisDetectWordsInText(text: str) -> str:

    text_lower = text.lower()
    correspondence = [phrases for phrases in phrases_crisis if phrases_crisis.lower() in text_lower]
    if not correspondence:
        return f"não encontrei nenhuma correspondencia"
    return correspondence

def audioRecognize(audioPath:str):

    try:
        with open(audioPath, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",
                language="pt",
                temperature=0.0
            )
            return transcription.text

    except Exception as e:
        return f"Error in recognize audio: {e}"
    