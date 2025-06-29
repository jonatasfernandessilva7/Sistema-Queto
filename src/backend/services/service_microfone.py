import time
import numpy as np
import threading
import sounddevice as sd
import datetime
import os

from groq import Groq
from scipy.io.wavfile import write
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

is_recording_flag = False
audio_data_buffer = []
samplerate_global = 44100
recording_thread = None
audio_file_path = None

def gravar_audio_microfone(samplerate=44100):

    global is_recording_flag, audio_data_buffer, samplerate_global, audio_file_path
    if is_recording_flag:
        return "Gravação já em andamento."

    print("Gravando áudio...")
    is_recording_flag = True
    audio_data_buffer = []
    samplerate_global = samplerate

    pasta = os.path.join(os.path.dirname(__file__), "..", "audios/")
    os.makedirs(pasta, exist_ok=True)
    audio_file_path = os.path.join(pasta, f"audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")


    def gravaAudio():
        with sd.InputStream(samplerate = samplerate, channels = 1, dtype = 'int16') as stream:
            while is_recording_flag:
                chunk, overflowed = stream.read(samplerate)
                print("li")
                audio_data_buffer.append(chunk)
                time.sleep(0.1)

        print("Thread de gravacao encerrada")
        if audio_data_buffer:
            final_audio = np.concatenate(audio_data_buffer, axis=0)
            write(audio_file_path, samplerate_global, final_audio)
            print(f"audio salvo em {audio_file_path}")
        else:
            print("nenhum audio foi gravado")

    global recording_thread
    recording_thread = threading.Thread(target=gravaAudio)
    recording_thread.start()
    return f"Gravação iniciada e será salva em {audio_file_path}"

def stop_recording_continuous():
    global is_recording_flag, recording_thread, audio_file_path
    if not is_recording_flag:
        return "Nenhuma gravação em andamento."

    print("Parando gravação contínua...")
    is_recording_flag = False
    if recording_thread and recording_thread.is_alive():
        recording_thread.join()

    if audio_file_path and os.path.exists(audio_file_path):
        caminho_final = audio_file_path
        audio_file_path = None
        return caminho_final
    else:
        return "Erro: O arquivo de áudio não foi salvo ou encontrado."


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