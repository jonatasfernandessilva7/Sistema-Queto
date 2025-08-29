import io
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
from src.AiServices.AiModels import EventModel
from src.backend.utils.ConnectionWithLlamaApiGroqUtils import llama_api_call
from src.backend.controllers.DocumentAnalysisController import pdf_local_analysis

ARCHIVES_FOR_CONTEXT_PATH = "../../uploads"
ANALYSIS_MODULE = pdf_local_analysis()
A_MATURITY_MODEL = "../../docs/A_maturity_model.pdf"

async def AiGeneretadReportsWithLlama(evento: EventModel, resposta: str, plano: list, prioridade: str) -> str:

    prompt = f"""
Generate a **Technical Risk and Crisis Report** in **Portuguese**, **following ABNT standards**, based on the information and parameters below.

**Objective:**
Produce a **formal, technical, and visually** organized document, suitable for corporate use, containing a risk assessment, potential crises, and an action plan.

**Input data:**

{{
  "event": "{evento.type}",
  "source": "{evento.origin}",
  "details": {json.dumps(evento.details, ensure_ascii=False)},
  "reactive_response": "{resposta}",
  "action_plan": {json.dumps(plano, ensure_ascii=False)},
  "priority": "{prioridade}"
}}

**Sources and context:**

- Use the files in the {ARCHIVES_FOR_CONTEXT_PATH} directory as a basis for characterizing the organizational context.

- Use the {ANALYSIS_MODULE} module to analyze these files.

- Consider the analysis summary as the organization's baseline context.

- Assess the level of organizational maturity and the ability to respond to risks and crises based on:
    - ISO 22325:2016
    - Article: A maturity model for enterprise risk management {A_MATURITY_MODEL}.

**Report Requirements:**

1. **Structure** in accordance with ABNT standards, with:

    - Cover (title, details, person responsible)

    - Summary

    - Introduction

    - Context of the Event

    - Analysis of Possible Risks and Crises

    - Escalation Scenarios

    - Action Plan (ISO 22361:2022 and ISO 31000:2018)

    - Priority Classification (ISO 22324:2022 – Low, Moderate, High, Critical, Extreme)

    - Calculation of Probability of Occurrence (Monte Carlo, 50,000 simulations per scenario)

    - Conclusion with confidence/accuracy level (%)

**2. Technical Content:**

    - Formal language and specialized terminology in risk and crisis management.

    - Visual clarity and organization to facilitate executive comprehension.

    - No irrelevant information or noise.

**3. Mandatory analysis:**

    - Relate the event to the organizational context found in the files.

    - Indicate potential risks, derived crises, and escalation methods.

    - Assess the impact of organizational modernity on crisis response.

    - Calculate the probability of each scenario occurring using the Monte Carlo method.

    - Determine the priority level according to ISO 22324:2022.

    - Present the confidence of the analysis as a percentage.

**4. Tone of the report:**

    - Professional, objective, and confident.

    - Based on evidence and technical standards.

**OBSERVAÇÃO**: Consider the full context of everything said. Even if there's some wording related to cybercrisis, if the context doesn't indicate a possible cybercrisis, don't raise the possibility of a crisis.
"""
    
    try:
            
        relatorio_final = await llama_api_call(prompt)

        return relatorio_final or "Relatório vazio gerado pela IA."
    
    except Exception as e:
            
        print(f"Erro ao gerar relatório com LLaMA via API (Groq): {e}")

        return f"Erro interno ao gerar relatório com a IA: {e}. Verifique logs."


def get_color_by_prioridade(prioridade: str):

    cores = {
        "Crítico": colors.red,
        "Alta": colors.orange,
        "Moderada": colors.yellow,
        "Baixa": colors.green,
        "Desconhecida": colors.gray
    }

    return cores.get(prioridade, colors.gray)

def AiSaveReports(relatorio_conteudo: str, timestamp: str, prioridade: str) -> str:

    pasta = os.path.join(os.path.dirname(__file__), "..", "relatorios/novos_relatorios")
    os.makedirs(pasta, exist_ok=True)
    nome_arquivo = os.path.join(pasta, f"relatorio_crise_{timestamp}.pdf")

    buffer = io.BytesIO()
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