from src.core.models import EventModel
from src.AiServices.AiMemory import atualizar_status_sistema
from src.core.utils.llama_api_utils import llama_api_call

def AiReactiveAnswer(evento: EventModel) -> str:

    if evento.type == "falha_sistema":

        sistema = evento.details.get("sistema")

        if sistema: 

            atualizar_status_sistema(sistema, "falho") 

            return f"Alert: The system '{sistema}' is down. Initiating contingency protocol."
        
        else:
            
            return "Alert: System failure detected, but the specific system was not identified. Initiating general contingency protocol."
    elif evento.type == "ataque_cibernetico":

        return "Alert: Cyber attack detected! Activating security team and blocking suspicious traffic."
    
    else:

        return "Alert: Event received. Awaiting analysis for reactive response."

def AiDeliberativePlanning(evento: EventModel) -> list[str]:

    if evento.type == "falha_sistema":

        return [
            "Notify the IT team about the system failure.",
            "Redirect user traffic to backup systems.",
            "Generate a preliminary report for the management."
        ]
    
    elif evento.type == "ataque_cibernetico":

        return [
            "Isolate affected systems to contain the propagation.",
            "Analyze security logs to identify the source and vector of the attack.",
            "Communicate with internal and external stakeholders according to the crisis communication plan."
        ]
    
    elif evento.type == "alerta_generico":

        return [
            "Collect more information about the alert.",
            "Evaluate the potential impact.",
            "Determine the team responsible for the investigation."
        ]
    
    else:

        return ["Monitor the situation and collect additional data for analysis."]

async def gerar_resposta_llama_api(prompt: str) -> str:
    try:

        resposta = await llama_api_call(prompt)

        return resposta.strip()
    
    except Exception as e:

        print(f"Error generating response with the AI (llama_api_call): {e}")

        return "Error generating response with the AI. Please try again."