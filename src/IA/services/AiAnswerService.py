from src.IA.AiModels import EventModel
from src.IA.AiMemory import atualizar_status_sistema
from src.backend.utils.ConnectionWithLlamaApiGroqUtils import llama_api_call

def AiReactiveAnswer(evento: EventModel) -> str:

    if evento.type == "falha_sistema":

        sistema = evento.details.get("sistema")

        if sistema: 

            atualizar_status_sistema(sistema, "falho") 

            return f"Alerta: O sistema '{sistema}' está fora do ar. Iniciando protocolo de contingência."
        
        else:
            
            return "Alerta: Falha de sistema detectada, mas o sistema específico não foi identificado. Iniciando protocolo de contingência geral."
        
    elif evento.type == "ataque_cibernetico":

        return "Ataque cibernético detectado! Acionando time de segurança e bloqueando tráfego suspeito."
    
    else:

        return "Evento recebido. Aguardando análise para resposta reativa."

def AiDeliberativePlanning(evento: EventModel) -> list[str]:

    if evento.type == "falha_sistema":

        return [
            "Notificar equipe de TI sobre a falha do sistema.",
            "Redirecionar o tráfego de usuários para sistemas de backup.",
            "Gerar relatório preliminar para a diretoria."
        ]
    
    elif evento.type == "ataque_cibernetico":

        return [
            "Isolar sistemas afetados para conter a propagação.",
            "Analisar logs de segurança para identificar a origem e o vetor do ataque.",
            "Comunicar stakeholders internos e externos conforme o plano de comunicação de crise."
        ]
    
    elif evento.type == "alerta_generico":

        return [
            "Coletar mais informações sobre o alerta.",
            "Avaliar o impacto potencial.",
            "Determinar a equipe responsável pela investigação."
        ]
    
    else:

        return ["Monitorar a situação e coletar dados adicionais para análise."]

async def gerar_resposta_llama_api(prompt: str) -> str:
    try:

        resposta = await llama_api_call(prompt)

        return resposta.strip()
    
    except Exception as e:

        print(f"Erro ao gerar resposta com a IA (llama_api_call): {e}")

        return "Erro ao gerar resposta com a IA. Por favor, tente novamente."