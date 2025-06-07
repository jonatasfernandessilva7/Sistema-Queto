from src.IA.services.service_resposta import gerar_resposta_llama_api
from src.backend.db.db import get_feedback_for_event_type

async def classificar_evento(detalhes_evento):

    prompt = f"""
    You are an AI specialized in corporate risks and crises...
    **Event Details:** {detalhes_evento}
    **Respond with only the event type, as a single word, in Portuguese.**
    """

    llm_resposta = await gerar_resposta_llama_api(prompt)
    classificacao_llm = llm_resposta.strip()

    feedbacks_recentes = get_feedback_for_event_type(classificacao_llm, limit=10) 
    human_overrides = [f['human_classification'] for f in feedbacks_recentes if f['human_classification'] != classificacao_llm]

    if len(human_overrides) > len(feedbacks_recentes) / 2: 

        classificacao_final = max(set(human_overrides), key=human_overrides.count)
        print(f"DEBUG: Classificação do LLM '{classificacao_llm}' corrigida para '{classificacao_final}' por feedback humano.")

        return classificacao_final

    return classificacao_llm