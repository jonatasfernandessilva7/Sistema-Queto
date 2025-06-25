import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import HTTPException
from scipy.io import wavfile
from dotenv import load_dotenv
from src.IA.modelos import Evento
from src.backend.services.service_analise_som import analisar_som_fourier, filtro_passa_baixa, detectar_padroes, salvar_espectrograma
from src.IA.memoria import (
    adicionar_evento_historico,
    comparar_com_eventos_passados
)
from src.backend.services.service_microfone import gravar_audio_microfone, reconhecer_fala, stop_recording_continuous
from src.IA.services.service_resposta import resposta_reativa, planejamento_deliberativo
from src.IA.aprendizado import classificar_evento
from src.IA.services.service_relatorios import gerar_relatorio_llama, salvar_relatorio
from src.backend.services.service_email_utils import enviar_email_com_anexos

load_dotenv()

async def iniciarGravacao():
    gravacao = gravar_audio_microfone()

    if gravacao is None:
        raise HTTPException(status_code=404, detail="Arquivo de áudio é nulo.")

    return gravacao

async def receber_e_processar_audio():

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho_temp = stop_recording_continuous()

    if "Nenhuma gravação" in caminho_temp or "Erro" in caminho_temp:
        raise HTTPException(status_code=400, detail=caminho_temp)

    try:

        if not os.path.exists(caminho_temp) or os.path.getsize(caminho_temp) == 0:
            raise HTTPException(status_code=500, detail="Arquivo de áudio gerado está vazio ou não existe.")

        rate, signal = wavfile.read(caminho_temp)

        if len(signal.shape) > 1:
            signal = signal[:, 0]

        resultado_analise = analisar_som_fourier(caminho_temp)

        detalhes_evento = {
            "caminho_audio": caminho_temp,
            "duracao_segundos": str(len(signal) / rate),  # Duração real
            "sample_rate": str(rate)
        }

        if "pico_frequencia" in resultado_analise and "pico_amplitude" in resultado_analise:
            detalhes_evento["pico_frequencia"] = str(resultado_analise["pico_frequencia"])
            detalhes_evento["pico_amplitude"] = str(resultado_analise["pico_amplitude"])
            detalhes_evento["status_analise_som"] = resultado_analise.get("status", "desconhecido")
        elif "erro" in resultado_analise:
            detalhes_evento["erro_analise_som"] = resultado_analise["erro"]

        signal_filtrado = filtro_passa_baixa(signal, rate)
        padrao = detectar_padroes(signal_filtrado, rate)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Gerar timestamp aqui
        espectrograma_path = salvar_espectrograma(signal, rate, timestamp)

        detalhes_evento["padrao_detectado"] = padrao
        detalhes_evento["espectrograma_path"] = espectrograma_path

        texto_falado = reconhecer_fala(caminho_temp)
        detalhes_evento["texto_falado"] = texto_falado

        tipo_evento_detectado = await classificar_evento(detalhes_evento)

        evento = Evento(
            tipo=tipo_evento_detectado,
            origem="microfone_local",
            detalhes=detalhes_evento
        )

        adicionar_evento_historico({"evento": evento.model_dump(), "timestamp": timestamp})

        resposta = resposta_reativa(evento)
        plano = planejamento_deliberativo(evento)
        prioridade = await classificar_evento(evento)  # Use o evento
        similaridade_msg, evento_similar = comparar_com_eventos_passados(evento)

        relatorio = await gerar_relatorio_llama(evento, resposta, plano, prioridade)
        arquivo = salvar_relatorio(relatorio, timestamp, prioridade)
        await enviar_email_com_anexos([arquivo, caminho_temp], os.getenv("EMAIL_DESTINO"))

        retorno = {
            "padrao_detectado": padrao,
            "resposta_reativa": resposta,
            "plano_acao": plano,
            "prioridade": prioridade,
            "relatorio": relatorio,
            "similaridade": similaridade_msg,
            "evento_similar": evento_similar,
            "espectrograma": espectrograma_path
        }
        return retorno

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo de áudio não encontrado após gravação.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante o processamento do áudio: {e}")