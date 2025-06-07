import sounddevice as sd
import datetime
import os

from groq import Groq
from scipy.io.wavfile import write
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

def gravar_audio_microfone(duracao=10, samplerate=44100):

    print("Gravando áudio...")

    audio = sd.rec(int(duracao * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()

    caminho_arquivo = f"audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    write(caminho_arquivo, samplerate, audio)
    print(f"Áudio salvo em {caminho_arquivo}")

    return caminho_arquivo

def reconhecer_fala(caminho_audio:str):

    try:

        with open(caminho_audio, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo", 
                language="pt", 
                temperature=0.0 
            )

            return transcription.text
        
    except Exception as e:

        return f"Erro ao reconhecer fala com Groq Whisper: {e}"