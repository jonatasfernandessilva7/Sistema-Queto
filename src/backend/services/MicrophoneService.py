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

def recordMicrophoneAudio(samplerate=44100):

    global is_recording_flag, audio_data_buffer, samplerate_global, audio_file_path
    if is_recording_flag:
        return "Gravação já em andamento."

    print("Recording audio meeting...")
    is_recording_flag = True
    audio_data_buffer = []
    samplerate_global = samplerate

    pasta = os.path.join(os.path.dirname(__file__), "..", "audios/")
    os.makedirs(pasta, exist_ok=True)
    audio_file_path = os.path.join(pasta, f"audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")

    def recordAudio():
        with sd.InputStream(samplerate = samplerate, channels = 1, dtype = 'int16') as stream:
            while is_recording_flag:
                chunk, overflowed = stream.read(samplerate)
                audio_data_buffer.append(chunk)
                time.sleep(0.1)

        if audio_data_buffer:
            final_audio = np.concatenate(audio_data_buffer, axis=0)
            write(audio_file_path, samplerate_global, final_audio)
            return {f"save audio in {audio_file_path}"}
        else:
            return {"no record audio"}

    global recording_thread
    recording_thread = threading.Thread(target=recordAudio)
    recording_thread.start()
    return f"initialize recording, save in {audio_file_path}"

def stopContinuousRecording():
    global is_recording_flag, recording_thread, audio_file_path
    if not is_recording_flag:
        return "No recordings in progress."

    is_recording_flag = False
    if recording_thread and recording_thread.is_alive():
        recording_thread.join()

    if audio_file_path and os.path.exists(audio_file_path):
        finalPathAudio = audio_file_path
        audio_file_path = None
        return finalPathAudio
    else:
        return "Error: audio file not found"


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