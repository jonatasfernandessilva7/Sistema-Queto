import os
import sys
import asyncio

# ensure project root is importable so `src` package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from src.api.services.reports import AiGeneretadReportsWithLlama, AiSaveReports


def test_ai_save_reports_creates_pdf(tmp_path):
    # Use unique timestamp so test file doesn't collide
    timestamp = "test_ts_12345"
    content = "# Relatório de Teste\nEste é um relatório de teste gerado pela suíte de testes."
    prioridade = "Baixa"

    path = AiSaveReports(content, timestamp, prioridade)

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0

    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass


def test_ai_generated_reports_monkeypatched(monkeypatch):
    # Monkeypatch the C2M function used by AiGeneretadReportsWithLlama
    async def fake_AiGenerateReportC2M(evento):
        return {
            "status": "success",
            "analysis_summary": "Relatório estruturado de teste"
        }

    # Patch AiGenerateReportC2M in the AiReportsService module
    from src.AiServices.services import AiReportsService
    monkeypatch.setattr(AiReportsService, 'AiGenerateReportC2M', fake_AiGenerateReportC2M)

    class DummyEvent:
        def model_dump(self):
            return {"type": "test", "origin": "local", "details": {}}

    result = asyncio.run(AiGeneretadReportsWithLlama(DummyEvent(), "resp", [], "tipo"))

    assert isinstance(result, str)
    assert "Relatório estruturado de teste" in result
