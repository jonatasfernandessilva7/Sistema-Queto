"""
Responsabilidades:
  - Executar o pipeline C2M completo (via C2MOrchestrator)
  - Serializar resultado em PDF estruturado (reportlab)
  - Manter compatibilidade com a assinatura legada AiGeneretadReportsWithLlama

Correção crítica aplicada:
  - ANALYSIS_MODULE não é mais executado em import-time como coroutine síncrona.
    A análise de documentos é feita de forma lazy dentro da função, evitando
    o bug de `asyncio.coroutine` atribuído a uma variável global.
"""

from __future__ import annotations

import io
import logging
import os
import re

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from src.agents.orchestrator.C2M_Orchestrator import C2MOrchestrator
from src.core.config.settings import Settings
from src.core.models import EventModel

log = logging.getLogger(__name__)

REPORTS_DIR = Settings.REPORTS_DIR / "novos_relatorios"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

_PRIORITY_COLOR_MAP = {
    "crítico": colors.red,
    "alta": colors.orange,
    "moderada": colors.yellow,
    "baixa": colors.green,
    "desconhecida": colors.gray,
}

async def AiGenerateReportC2M(evento: EventModel) -> Dict:
    """
    Executa o pipeline C2M completo de 4 estágios e devolve o resultado
    como dicionário JSON-serializável.

    Returns
    -------
    dict
        Chaves: status, mean_probability, mean_probability_pct, priority,
        iso_22324, confidence_interval_95, percentiles, pearson_correlations,
        std_deviation, conformity_factor, sentiment, risk_agents,
        organizational_context, crisis_scenarios, decision_tree,
        analysis_summary, low_risk_assessment
    """
    orchestrator = C2MOrchestrator()
    result = await orchestrator.process_event(evento, use_llm_enhancement=True)
    return result


async def AiGeneretadReportsWithLlama(
    evento: EventModel,
    resposta: str = None,      # ignorado — mantido por compatibilidade
    plano: list = None,        # ignorado — mantido por compatibilidade
    type_event: str = None,    # ignorado — mantido por compatibilidade
) -> str:
    """
    Interface legada: executa o pipeline C2M e retorna o sumário como string.

    Os parâmetros resposta, plano e type_event são ignorados — o modelo C2M
    completo substitui esses passos manuais.
    """
    log.info("AiGeneretadReportsWithLlama → delegando ao pipeline C2M")

    try:
        result = await AiGenerateReportC2M(evento)

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error_message", "Erro desconhecido no pipeline C2M"),
            )

        return result.get("analysis_summary", "Relatório gerado pelo modelo C2M.")

    except HTTPException:
        raise
    except Exception as exc:
        log.error("Erro ao gerar relatório C2M: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {exc}")

def get_color_by_prioridade(prioridade: str) -> colors.Color:
    """Mapeia prioridade para cor reportlab (ISO 22324)."""
    return _PRIORITY_COLOR_MAP.get(prioridade.lower(), colors.gray)


def AiSaveReports(
    relatorio_conteudo: str,
    timestamp: str,
    prioridade: str,
) -> str:
    """
    Persiste o conteúdo do relatório como PDF em REPORTS_DIR.

    Returns
    -------
    str
        Caminho absoluto do arquivo PDF gerado.
    """
    output_path = REPORTS_DIR / f"relatorio_crise_{timestamp}.pdf"
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    cor_alerta = get_color_by_prioridade(prioridade)

    priority_style = ParagraphStyle(
        name="Prioridade",
        parent=styles["Heading2"],
        textColor=cor_alerta,
        fontSize=16,
        spaceAfter=12,
    )

    story = [
        Paragraph("<b>Sistema Queto — Relatório de Probabilidade de Crise Cibernética</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"<b>Data e Hora:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles["Normal"]),
        Spacer(1, 6),
        Paragraph(f"<b>Nível de Prioridade (ISO 22324):</b> {prioridade}", priority_style),
        Spacer(1, 12),
    ]

    for linha in relatorio_conteudo.strip().splitlines():
        if not linha.strip():
            continue

        texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", linha.strip())
        texto = re.sub(r"\*(.+?)\*", r"<i>\1</i>", texto)

        if texto.startswith("# "):
            story.append(Paragraph(texto[2:], styles["h1"]))
        elif texto.startswith("## "):
            story.append(Paragraph(texto[3:], styles["h2"]))
        elif texto.startswith("### "):
            story.append(Paragraph(texto[4:], styles["h3"]))
        else:
            story.append(Paragraph(texto, styles["Normal"]))

        story.append(Spacer(1, 6))

    # Imagem de referência ISO 22324 (opcional)
    img_path = Path(__file__).parent / ".." / "image" / "matriz_alerta_iso22324.png"
    if img_path.exists():
        story.extend([
            Spacer(1, 12),
            Paragraph("<b>Código de Cores — ISO 22324:</b>", styles["Normal"]),
            Spacer(1, 6),
            RLImage(str(img_path), width=16 * cm, height=2 * cm),
        ])

    try:
        doc.build(story)
        log.info("Relatório PDF salvo: %s", output_path)
        return str(output_path)
    except Exception as exc:
        log.error("Erro ao construir PDF: %s", exc)
        raise RuntimeError(f"Erro ao salvar relatório PDF: {exc}") from exc
