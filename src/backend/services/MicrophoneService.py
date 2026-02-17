import time
import numpy as np
import threading
import sounddevice as sd
import datetime
import os
import logging

from groq import Groq
from scipy.io.wavfile import write
from dotenv import load_dotenv
from src.core.config.settings import Settings

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

log = logging.getLogger(__name__)

class AudioRecorder:
    """Thread-safe audio recording manager."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.is_recording = False
        self.audio_buffer = []
        self.samplerate = 44100
        self.recording_thread = None
        self.audio_file_path = None
    
    def start_recording(self, samplerate=44100) -> str:
        """Start audio recording in a background thread."""
        with self._lock:
            if self.is_recording:
                return "Gravação já em andamento."
            
            log.info("Recording audio meeting...")
            self.is_recording = True
            self.audio_buffer = []
            self.samplerate = samplerate
            
            pasta = Settings.AUDIOS_DIR
            pasta.mkdir(parents=True, exist_ok=True)
            self.audio_file_path = str(pasta / f"audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
            
            self.recording_thread = threading.Thread(target=self._record_audio, daemon=False)
            self.recording_thread.start()
            return f"initialize recording, save in {self.audio_file_path}"
    
    def _record_audio(self) -> None:
        """Internal method to record audio (runs in background thread)."""
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='int16') as stream:
                while self.is_recording:
                    chunk, _ = stream.read(self.samplerate)
                    with self._lock:
                        self.audio_buffer.append(chunk)
                    time.sleep(0.1)
            
            with self._lock:
                if self.audio_buffer:
                    final_audio = np.concatenate(self.audio_buffer, axis=0)
                    write(self.audio_file_path, self.samplerate, final_audio)
                    log.info(f"Audio saved to {self.audio_file_path}")
        except Exception as e:
            log.error(f"Error during audio recording: {e}")
    
    def stop_recording(self) -> str:
        """Stop the ongoing recording and return the file path."""
        with self._lock:
            if not self.is_recording:
                return "No recordings in progress."
            
            self.is_recording = False
        
        # Wait for thread to finish (outside lock to avoid deadlock)
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        
        with self._lock:
            if self.audio_file_path and os.path.exists(self.audio_file_path):
                result = self.audio_file_path
                self.audio_file_path = None
                return result
            else:
                log.warning("Audio file not found after recording")
                return "Error: audio file not found"

# Global instance for backward compatibility
_recorder = AudioRecorder()

def recordMicrophoneAudio(samplerate=44100):
    """Public API for starting recording."""
    return _recorder.start_recording(samplerate)

def stopContinuousRecording():
    """Public API for stopping recording."""
    return _recorder.stop_recording()