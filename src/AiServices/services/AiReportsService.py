import io
import os
import json
import re
import logging
import asyncio

from fastapi import HTTPException
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from src.core.models import EventModel
from src.core.utils.llama_api_utils import llama_api_call
from src.core.config.settings import Settings
from src.agents.orchestrator.C2M_Orchestrator import C2MOrchestrator
from src.agents.orchestrator.C2M_Models import ISO_22324_COLORS, ISO_22324_LEVELS
from src.backend.repository.GenericsRepository import saveReport

log = logging.getLogger(__name__)

ARCHIVES_FOR_CONTEXT_PATH = Settings.UPLOADS_DIR
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

def AiSaveReports(
    relatorio_conteudo: str,
    timestamp: str,
    prioridade: str,
    documento_id: Optional[int] = None,
) -> str:
    """
    Gera o PDF do relatório em disco e persiste o conteúdo no banco de dados.

    Parameters
    ----------
    relatorio_conteudo : str
        Texto do relatório (suporta markdown simples: #, ##, ###, **bold**, *italic*).
    timestamp : str
        Usado como sufixo do nome do arquivo (formato %Y%m%d_%H%M%S).
    prioridade : str
        Nível ISO 22324: Crítico / Alta / Moderada / Baixa / Desconhecida.
    documento_id : int | None
        ID do documento corporativo relacionado, ou None para relatórios
        gerados a partir de áudio / eventos de texto.

    Returns
    -------
    str
        Caminho absoluto do arquivo PDF gerado.

    Raises
    ------
    RuntimeError
        Se a construção do PDF ou a persistência no banco falharem.
    """
    pasta = Settings.REPORTS_DIR / "novos_relatorios"
    pasta.mkdir(parents=True, exist_ok=True)
    nome_arquivo = str(pasta / f"relatorio_crise_{timestamp}.pdf")

    # ── Construir PDF em disco ────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    cor_alerta = get_color_by_prioridade(prioridade)

    estilo_prioridade = ParagraphStyle(
        name="Prioridade",
        parent=styles["Heading2"],
        textColor=cor_alerta,
        fontSize=16,
        spaceAfter=12,
    )

    story = []
    story.append(Paragraph("<b>Sistema Queto — Relatório de Probabilidade de Crise Cibernética</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Data e Hora:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Nível de Prioridade (ISO 22324):</b> {prioridade}", estilo_prioridade))
    story.append(Spacer(1, 12))

    for linha in relatorio_conteudo.strip().split("\n"):
        if not linha.strip():
            continue
        linha_formatada = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", linha.strip())
        linha_formatada = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", linha_formatada)

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
        story.append(Paragraph("<b>Código de Cores de Alerta — ISO 22324:</b>", styles["Normal"]))
        story.append(Spacer(1, 6))
        story.append(RLImage(caminho_img, width=16 * cm, height=2 * cm))

    try:
        doc.build(story)
        log.info("PDF gerado em disco: %s", nome_arquivo)
    except Exception as exc:
        log.error("Erro ao construir PDF: %s", exc)
        raise RuntimeError(f"Erro ao gerar PDF do relatório: {exc}") from exc

    # ── Persistir no banco (tabela analise_de_documentos) ────────────────────
    try:
        pdf_bytes = Path(nome_arquivo).read_bytes()
        report_id = saveReport(documento_id, pdf_bytes)
        log.info("Relatório persistido no banco: report_id=%d documento_id=%s", report_id, documento_id)
    except Exception as exc:
        # Não impede o fluxo — o PDF já foi gerado em disco
        log.error("Falha ao persistir relatório no banco (PDF em disco preservado): %s", exc)

    return nome_arquivo