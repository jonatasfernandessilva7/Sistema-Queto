import soundfile as sf
import numpy as np
import os

from scipy.fft import fft, fftfreq
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt

def audioAnalysisWithFft(file:str):

    try:
        data, samplerate = sf.read(file)
        if len(data.shape) > 1: 
            data = data[:, 0]
        N = len(data) 
        yf = fft(data) 
        xf = fftfreq(N, 1 / samplerate) 
        idx = np.where(xf > 0) 
        frequency = xf[idx]
        amplitudes = np.abs(yf[idx])
        peak_frequency = frequency[np.argmax(amplitudes)]
        peak_amplitude = np.max(amplitudes)

        return {
            "peak_frequency": float(peak_frequency),
            "peak_amplitude": float(peak_amplitude),
            "status": "analyzed"
        }
    
    except Exception as e:
        return {"error": str(e)}

def audioAnalysisLowPassFilter(signal, rate, cutoff=4000):

    nyquist = 0.5 * rate
    normal_cutoff = cutoff / nyquist
    b, a = butter(6, normal_cutoff, btype='low', analog=False)

    return lfilter(b, a, signal)

def audioAnalysisDetectPatterns(signal, rate):

    energy = np.sum(signal ** 2)

    if energy > 1e12:
        return "detected explosion"
    elif np.mean(np.abs(signal)) > 1000:
        return "alarm"
    elif energy == 0:
        return "calm environment"
    else:
        return "situation not identified"

def saveSpectogram(signal, rate, timestamp):

    folder = "../relatorios/espectogramas"
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"espectrograma_{timestamp}.png")

    plt.figure(figsize=(10, 4))
    plt.specgram(signal, Fs=rate, NFFT=1024, noverlap=512, cmap='inferno')
    plt.title("Espectrograma de Áudio")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Frequência (Hz)")
    plt.colorbar(label='Intensidade')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path