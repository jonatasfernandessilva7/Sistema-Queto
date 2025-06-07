import soundfile as sf
import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt
import os

def analisar_som_fourier(file:str):

    try:

        data, samplerate = sf.read(file) 

        if len(data.shape) > 1: 
            data = data[:, 0]

        N = len(data) 
        yf = fft(data) 
        xf = fftfreq(N, 1 / samplerate) 
        idx = np.where(xf > 0) 
        frequencias = xf[idx]
        amplitudes = np.abs(yf[idx])
        pico_frequencia = frequencias[np.argmax(amplitudes)] 
        pico_amplitude = np.max(amplitudes) 

        return {
            "pico_frequencia": float(pico_frequencia),
            "pico_amplitude": float(pico_amplitude),
            "status": "analisado"
        }
    
    except Exception as e:

        return {"erro": str(e)}

def filtro_passa_baixa(signal, rate, cutoff=4000):

    nyquist = 0.5 * rate
    normal_cutoff = cutoff / nyquist
    b, a = butter(6, normal_cutoff, btype='low', analog=False)

    return lfilter(b, a, signal)

def detectar_padroes(signal, rate):

    energia = np.sum(signal ** 2)

    if energia > 1e12:
        return "Explosão detectada"
    
    elif np.mean(np.abs(signal)) > 1000:
        return "Grito ou alarme detectado"   
    
    else:
        return "Ambiente calmo ou desconhecido"

def salvar_espectrograma(signal, rate, timestamp):

    pasta = "../relatorios/espectogramas"
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"espectrograma_{timestamp}.png")

    plt.figure(figsize=(10, 4))
    plt.specgram(signal, Fs=rate, NFFT=1024, noverlap=512, cmap='inferno')
    plt.title("Espectrograma de Áudio")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Frequência (Hz)")
    plt.colorbar(label='Intensidade')
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()

    return caminho