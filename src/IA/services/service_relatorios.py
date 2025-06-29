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
from src.IA.modelos import Evento
from src.backend.services.service_llama_api import llama_api_call
from src.backend.controllers.controller_relatorios import salva_os_relatorios
from src.backend.controllers.controller_analise_de_documentos import analisar_pdf_local

ARCHIVES_FOR_CONTEXT_PATH = "../../uploads"
ANALYSIS_MODULE = analisar_pdf_local()

async def gerar_relatorio_llama(evento: Evento, resposta: str, plano: list, prioridade: str) -> str:

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

consider the "files" in the path {ARCHIVES_FOR_CONTEXT_PATH}. use {ANALYSIS_MODULE} for analysis of files. consider the summary made in the analysis and use it as organizational context.
analyze the "maturity level" and capacity of the organization to deal with risks and crises. For this analysis, consider the files in the path. Consider **ISO 22325:2022** and the article **A Maturity Model for Enterprise Risk Management** que está disponível em: https://pdf.sciencedirectassets.com/271692/1-s2.0-S0925527315X00181/1-s2.0-S0925527315005320/main.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEGIaCXVzLWVhc3QtMSJHMEUCIQCkakTDYS1%2ByykbS9CNnbQCZTxGWJ9%2Fb0LIoR5QfIZH7wIgZVeVEpvBCsMFptAd%2F%2F8LpCp2geMRBDBE9RPKAohiVdAqswUIWxAFGgwwNTkwMDM1NDY4NjUiDJHZ6gbvwzduZu5OIyqQBV3O1hzJCiaGbu5U%2F6GG2g6YfVpVihUihvqx6VpxxkCuaBac64h3WVUbkIu8bFLVkDBUte3xTrh%2BUJUOZk%2BXsoUqlwDIbhGE2w0xVtN3K7qtsoVUostIfsxMBrtYm6DNT9TY6znk6VFElugPkXxVKroHWsd9jjPLhKRvI0%2BPuYtPClhJBStSvFHoynQhZ%2FmN1pO%2FIdNRevTSpvLeIgWEY0sKU%2B2cOWpAjhfrwsSuii4opELiw7Oxf9tuzp4npKPvgKSyGnRaAHS3sEZjs8mvMCV4WbWBaQZYTMe7Jf9RJ%2FHJG7kk5jA23S5JBJk7Zs8WHIVJHLdqsTNdzaYiLxLVAfd3elFWfR%2FzeL0hnyWEfewnodwhsXJv%2FL3UsNeSlsYPMYdCTz1dUKfZPJX9Acw2AqsK5GJusA5tvbey9ClajJChPCPkNj4Qym1AbaPO2p5exOQH369pq3s%2F7HeUGfxY2b%2BwesQ3oGFQZJYKz35qWiakKzATr3qGJD4oMyqe4JLZz4qXD93b3mi3A9idIWVb%2BZVUARi06Xa0ktr9gLhgi1bRV9hanb6S6dyk5arTuajfYNHaVPe5Ns6MtD9DsMgZpYuQJkXuKYg1vnOuf%2B4HS9zK08pjCGVDndObfZCXtACeMIllgzunI2%2Fr%2BN2PlV5Q5yOhvA6WPr5oSKCSr23O5tME%2BozKmP7iJcV1R6zFB2whladG%2BSNfhwZgVpdKT2j61DWBdbOnOt%2BQsXBBdPZu9pei%2Fv0Y5DAQI1lL3Vk9q0lA31SxyuofqSVBO%2F0%2FIMJ5yvtX83Y%2BD%2BIwZRIdXEekX%2BK8Uf5T2FAsNNgZ72SYCUI9XDov5gwug%2F7f1Prjfdw%2BfBu29rTm3OfAEgFEAoLnm3uHMI%2Bo9MIGOrEBh1QQqlWECZvcumGyt2Bmxaj%2FsAT7u%2BqJJt0k9ndvPGEvwvIY6EClbwqq7KfeLfcdnvx1LfMvxNCLNUyr7PtM%2Bq3LgBPz8ijTEK2kqDXojJlofbNCRQj3rKlaWbj6fiINv%2Fg31dqDHW42VQ6Dj5fikY42kYdXD%2FNZXzieKgEjVxNRGUkm3Y%2FD34Ycc6OkrJssccBsTNm6L%2FF%2BVU0kdFMjRd8NH3nw9ljMn34qcjMyuXcz&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20250626T103131Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAQ3PHCVTYVWD27XQD%2F20250626%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=6fcf2fd223bb23777442fd269e6c9f02337d6a6d11f0a384a519e9ab48eb2872&hash=79d846f52de0b950ca2cca03a4abb30351fd69b9244055c6378e276cb3732610&host=68042c943591013ac2b2430a89b270f6af2c76d8dfd086a07176afe7c76c2c61&pii=S0925527315005320&tid=spdf-66e2c06f-2eb0-4724-b32c-f4c86eee8730&sid=56e24e373095e04e872a9957916f220c902fgxrqa&type=client&tsoh=d3d3LnNjaWVuY2VkaXJlY3QuY29t&rh=d3d3LnNjaWVuY2VkaXJlY3QuY29t&ua=18105c5550015f5d5350&rr=955c09126b2af637&cc=br

The report must take into account:
1. the context in which the organization operates, given the files analyzed
2. the level of maturity of the organization

**Report Requirements:**
- Include a clear description of the event and its context.
- Given the **maturity level** of the organization and **files** in {ARCHIVES_FOR_CONTEXT_PATH}, explain potential risks and escalation scenarios.
- Develop the **action plan** based on the principles of **ISO 22361:2022** (Crisis Management) and **ISO 31000:2018** (Risk Management).
- Given **event** , classify the **priority level** of the event using the **ISO 22324:2022** color system (e.g. Low, Moderate, High, Critical, Extreme - use these terms in Portuguese).
- Calculate the chance of any of the possible crises found occurring. To do this, use the Monte Carlo method with 50,000 simulations for each crisis scenario found.
- Conclude the report by indicating the **confidence level** or **accuracy** of the analysis, values always in **percentage**.

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

    cores = {
        "Crítico": colors.red,
        "Alta": colors.orange,
        "Moderada": colors.yellow,
        "Baixa": colors.green,
        "Desconhecida": colors.gray
    }

    return cores.get(prioridade, colors.gray)

def salvar_relatorio(relatorio_conteudo: str, timestamp: str, prioridade: str) -> str:

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