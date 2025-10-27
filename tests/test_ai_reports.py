import os
import sys
import asyncio

# ensure project root is importable so `src` package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from src.AiServices.services import AiReportsService


def test_ai_save_reports_creates_pdf(tmp_path):
    # Use unique timestamp so test file doesn't collide
    timestamp = "test_ts_12345"
    content = "# Relatório de Teste\nEste é um relatório de teste gerado pela suíte de testes."
    prioridade = "Baixa"

    path = AiReportsService.AiSaveReports(content, timestamp, prioridade)

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0

    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass


def test_ai_generated_reports_monkeypatched(monkeypatch):
    # Monkeypatch the agent function used by AiGeneretadReportsWithLlama
    async def fake_generateStructuredReport(evento, plano):
        return "Relatório estruturado de teste"

    # The service imports generateStructuredReport at module scope; patch the attribute in the service module
    monkeypatch.setattr(AiReportsService, 'generateStructuredReport', fake_generateStructuredReport)

    class DummyEvent:
        def model_dump(self):
            return {"type": "test", "origin": "local", "details": {}}

    result = asyncio.run(AiReportsService.AiGeneretadReportsWithLlama(DummyEvent(), "resp", [], "tipo"))

    assert isinstance(result, str)
    assert "Relatório estruturado de teste" in result
