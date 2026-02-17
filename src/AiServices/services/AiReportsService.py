import io
import os
import json
import re
import logging
import asyncio

from fastapi import HTTPException
from datetime import datetime
from typing import Dict
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from src.core.models import EventModel
from src.backend.utils.ConnectionWithLlamaApiGroqUtils import llama_api_call
from src.backend.controllers.DocumentAnalysisController import pdf_local_analysis
from src.core.config.settings import Settings
from src.agents.orchestrator.C2M_Orchestrator import C2MOrchestrator
from src.agents.orchestrator.C2M_Models import ISO_22324_COLORS, ISO_22324_LEVELS

log = logging.getLogger(__name__)

ARCHIVES_FOR_CONTEXT_PATH = Settings.UPLOADS_DIR
ANALYSIS_MODULE = pdf_local_analysis()
A_MATURITY_MODEL = "../../docs/A_maturity_model.pdf"
PRIORITY_LEVELS = ["Desconhecida", "Baixa", "Moderada", "Alta", "Crítico"]
REPORTS_PATH = Settings.REPORTS_DIR / "novos_relatorios"
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════════
# NOVO: AiGenerateReportC2M - Usando modelo C2M completo
# ════════════════════════════════════════════════════════════════════════════════

async def AiGenerateReportC2M(evento: EventModel) -> Dict:
    """
    NOVO: Processa evento conforme modelo C2M com 4 estágios:
    1. Extração (3 supervisores)
    2. Decision Tree
    3. Monte Carlo (50.000 simulações)
    4. Relatório estruturado
    
    Args:
        evento: EventModel com type, origin, details
    
    Returns:
        Dict com resultado completo da análise C2M
    """
    
    orchestrator = C2MOrchestrator()
    result = await orchestrator.process_event(evento, use_llm_enhancement=True)
    
    return result


# ════════════════════════════════════════════════════════════════════════════════
# LEGACY: AiGeneretadReportsWithLlama - Mantido para compatibilidade
# (Agora usa C2M internamente)
# ════════════════════════════════════════════════════════════════════════════════

async def AiGeneretadReportsWithLlama(evento: EventModel, resposta: str = None, plano: list = None, type_event: str = None) -> str:
    """
    COMPATÍVEL COM LEGADO
    Mantém assinatura original mas executa C2M internamente
    
    Parâmetros resposta, plano, type_event são ignorados
    Evento é o único parâmetro usado
    """
    
    log.info(f"AiGeneretadReportsWithLlama chamado. Usando C2M...")
    
    try:
        result = await AiGenerateReportC2M(evento)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error_message"))
        
        # Retornar sumário como string para manter compatibilidade
        return result.get("analysis_summary", "Relatório gerado")
    
    except Exception as e:
        log.error(f"Erro ao gerar relatório C2M: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")


def get_color_by_prioridade(prioridade: str) -> colors.Color:
    """
    Retorna cor reportlab baseada em prioridade ISO 22324
    """
    
    # Mapeamento para colors reportlab
    cores = {
        "Crítico": colors.red,
        "crítico": colors.red,
        "Alta": colors.orange,
        "alta": colors.orange,
        "Moderada": colors.yellow,
        "moderada": colors.yellow,
        "Baixa": colors.green,
        "baixa": colors.green,
        "Desconhecida": colors.gray,
        "desconhecida": colors.gray
    }
    
    return cores.get(prioridade, colors.gray)

def AiSaveReports(relatorio_conteudo: str, timestamp: str, prioridade: str) -> str:

    pasta = Settings.REPORTS_DIR / "novos_relatorios"
    pasta.mkdir(parents=True, exist_ok=True)
    nome_arquivo = str(pasta / f"relatorio_crise_{timestamp}.pdf")

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

    story.append(Paragraph(f"<b>Tipo:</b> {prioridade}", estilo_prioridade))
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