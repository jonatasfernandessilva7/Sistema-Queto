import os
import json
import re

from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from src.IA.modelos import Evento
from src.backend.services.service_llama_api import llama_api_call 

async def gerar_relatorio_llama(evento: Evento, resposta: str, plano: list, prioridade: str) -> str:

    """
    Gera o conteúdo de um relatório de risco e crise detalhado usando a API LLaMA.
    Agora é assíncrona e usa 'await'.
    """

    prompt = f"""
You are an expert in corporate risk and crisis management. Based on the information provided, generate a **detailed risk and crisis report in Portuguese**, following the **ABNT formatting rules**.

The report should be:
- Visually well structured and easy to understand.
- Written in a formal tone, with **technical terminology** where appropriate.
- Free from irrelevant information or noise.
- Focused on describing **potential crises** that may arise from the detected **event**.

Use the following structured data:

{{
  "event": "{evento.tipo}",
  "source": "{evento.origem}",
  "details": {json.dumps(evento.detalhes, ensure_ascii=False)},
  "reactive_response": "{resposta}",
  "action_plan": {json.dumps(plano, ensure_ascii=False)},
  "priority": "{prioridade}"
}}

**Report Requirements:**
- Include a clear description of the event and its context.
- Explain potential risks and escalation scenarios.
- Develop the **action plan** based on the principles of **ISO 22361:2022** (Crisis Management) and **ISO 31000:2018** (Risk Management).
- Given **event** , classify the **priority level** of the event using the **ISO 22324:2022** color system (e.g. Low, Moderate, High, Critical, Extreme - use these terms in Portuguese).
- Calculate the chance of any of the possible crises found occurring. To do this, use the Monte Carlo method with 50,000 simulations for each crisis scenario found.
- Conclude the report by indicating the **confidence level** or **accuracy** of the analysis, values ​​always in **percentage**.

Do not include comments or explanations outside the content of the report.

Write the entire response in **Portuguese**, maintaining a professional, calm and expert tone.
"""
    
    try:
            
        relatorio_final = await llama_api_call(prompt)

        return relatorio_final or "Relatório vazio gerado pela IA."
    
    except Exception as e:
            
        print(f"Erro ao gerar relatório com LLaMA via API (Groq): {e}")

        return f"Erro interno ao gerar relatório com a IA: {e}. Verifique logs."


def get_color_by_prioridade(prioridade: str):

    """
    Retorna a cor ReportLab baseada no nível de prioridade.
    """

    cores = {
        "Crítico": colors.red, # Ajustado para 'Crítico' conforme prompt
        "Alta": colors.orange, # Ajustado para 'Alta'
        "Moderada": colors.yellow, # Ajustado para 'Moderada'
        "Baixa": colors.green, # Ajustado para 'Baixa'
        "Desconhecida": colors.gray # Ajustado para 'Desconhecida'
    }

    return cores.get(prioridade, colors.gray)

def salvar_relatorio(relatorio_conteudo: str, timestamp: str, prioridade: str = "Desconhecida") -> str:

    """
    Salva o conteúdo do relatório em um arquivo PDF.
    Esta função permanece síncrona, pois operações de arquivo são geralmente bloqueantes.
    """

    pasta = os.path.join(os.path.dirname(__file__), "..", "relatorios/novos_relatorios")
    os.makedirs(pasta, exist_ok=True)
    nome_arquivo = os.path.join(pasta, f"relatorio_crise_{timestamp}.pdf")

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()

    cor_alerta = get_color_by_prioridade(prioridade)

    estilo_prioridade = ParagraphStyle(
        name="Prioridade",
        parent=styles["Heading2"],
        textColor=cor_alerta,
        fontSize=16,
        spaceAfter=12
    )

    story = []

    story.append(Paragraph("<b>Sistema Queto - Relatório de Probabilidade de Crise</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Data e Hora:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph(f"<b>Nível de Prioridade:</b> {prioridade}", estilo_prioridade))
    story.append(Spacer(1, 12))

    for linha in relatorio_conteudo.strip().split("\n"):

        if linha.strip():
            linha_formatada = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", linha.strip())
            linha_formatada = re.sub(r"\*(.+?)\*", r"<i>\1</i>", linha_formatada) 

            if linha_formatada.startswith("# "):
                story.append(Paragraph(linha_formatada[2:], styles["h1"]))
            elif linha_formatada.startswith("## "):
                story.append(Paragraph(linha_formatada[3:], styles["h2"]))
            elif linha_formatada.startswith("### "):
                story.append(Paragraph(linha_formatada[4:], styles["h3"]))
            else:
                story.append(Paragraph(linha_formatada, styles["Normal"]))

            story.append(Spacer(1, 6))

    caminho_img = os.path.join(os.path.dirname(__file__), "..", "image", "matriz_alerta_iso22324.png")

    if os.path.exists(caminho_img):
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Código de Cores de Alerta Baseado na ISO 22324:</b>", styles["Normal"]))
        story.append(Spacer(1, 6))
        story.append(RLImage(caminho_img, width=16*cm, height=2*cm))
    else:
        print(f"Aviso: Imagem da matriz de alerta não encontrada em {caminho_img}")
        story.append(Spacer(1, 12))
        story.append(Paragraph("<i>(Imagem do código de cores não disponível)</i>", styles["Italic"]))


    try:

        doc.build(story)

        return nome_arquivo
    
    except Exception as e:

        print(f"Erro ao construir o PDF: {e}")
        
        return f"Erro ao salvar o relatório em PDF: {e}"