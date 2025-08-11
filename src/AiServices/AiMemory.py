import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from src.AiServices.AiModels import EventModel
from src.backend.repository.GenericsRepository import (
    add_event_history, get_event_history, get_memory_state,
    update_system_status, get_system_status
)

def AiCompareEventsHistory(evento_atual: EventModel):
    historico = get_event_history()

    if not historico:
        return "Nenhum evento semelhante encontrado.", None

    documentos = [
        json.dumps(e['evento']) for e in historico
    ] + [json.dumps(evento_atual.model_dump())]

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(documentos)

    similaridades = cosine_similarity(tfidf[-1], tfidf[:-1])
    indice_mais_similar = np.argmax(similaridades)
    maior_similaridade = similaridades[0, indice_mais_similar]

    if maior_similaridade > 0.3:
        evento_similar = historico[indice_mais_similar]['evento'] 
        return f"Evento semelhante encontrado com similaridade {maior_similaridade:.2f}", evento_similar

    return "Nenhum evento semelhante encontrado.", None

def getEventHistory():
    return get_event_history()

def AiAddingEventHistory(evento_com_timestamp: dict):

    event_data = evento_com_timestamp['event']
    timestamp = evento_com_timestamp['timestamp']
    add_event_history(event_data, timestamp)

def obter_estado_memoria():
    return get_memory_state()

def clusterEvents(historico, k=3):
    if len(historico) < k:
        return {"erro": f"Número de clusters {k} maior que eventos disponíveis."}

    textos = [json.dumps(ev["evento"]) for ev in historico]

    vetorizar = TfidfVectorizer()
    vetores = vetorizar.fit_transform(textos)

    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10) 
    clusters = kmeans.fit_predict(vetores)

    eventos_por_cluster = {i: [] for i in range(k)}
    for i, cluster_id in enumerate(clusters):
        eventos_por_cluster[cluster_id].append(historico[i])

    return eventos_por_cluster

def atualizar_status_sistema(system_name: str, status: str):
    update_system_status(system_name, status)

def obter_status_sistema(system_name: str):
    return get_system_status(system_name)