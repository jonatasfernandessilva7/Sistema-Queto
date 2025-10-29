import os
import sys
import asyncio

# make sure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

import src.agents.risk_agents.RiskAnalysisAgents as agents


class FakeResponse:
    def __init__(self, content="fake reply", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class FakeChat:
    def __init__(self, *args, **kwargs):
        pass

    def bind_tools(self, tools):
        self._tools = tools
        return self

    def invoke(self, messages):
        # return an object similar to what callLlama expects
        return FakeResponse(content="ok", tool_calls=[])


@pytest.mark.asyncio
async def test_monitoring_app_runs(monkeypatch):
    # Patch ChatGroq to avoid external API calls
    monkeypatch.setattr(agents, 'ChatGroq', FakeChat)

    # invoke the monitoring agent
    res = await agents.monitoring_app.ainvoke({"messages": [{"role": "user", "content": "Analise políticas de risco e controles"}]})
    assert isinstance(res, dict)
    assert 'messages' in res


@pytest.mark.asyncio
async def test_response_app_runs(monkeypatch):
    monkeypatch.setattr(agents, 'ChatGroq', FakeChat)
    res = await agents.response_app.ainvoke({"messages": [{"role": "user", "content": "Analise resposta a risco"}]})
    assert isinstance(res, dict)
    assert 'messages' in res


@pytest.mark.asyncio
async def test_plan_app_runs(monkeypatch):
    monkeypatch.setattr(agents, 'ChatGroq', FakeChat)
    res = await agents.plan_app.ainvoke({"messages": [{"role": "user", "content": "Analise plano de risco"}]})
    assert isinstance(res, dict)
    assert 'messages' in res
