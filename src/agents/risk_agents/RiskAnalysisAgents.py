import operator
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from typing import (
    Annotated,
    Sequence,
    TypedDict
)

from langchain_core.messages import (
    BaseMessage,
    ToolMessage
)
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# Document analysis utilities
from src.api.services.analysis import (
    extract_text,
    extract_tables,
    extract_images,
    resume_text
)
from src.backend.services.DocumentAnalysisService import (
    ocrMethod,
    semanticSearch
)

GROQ_API_KEY = os.getenv("API_KEY")


def _list_upload_files(upload_dir="uploads"):
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", upload_dir))
    if not os.path.exists(base):
        return []
    entries = [os.path.join(base, f) for f in os.listdir(base) if os.path.isfile(os.path.join(base, f))]
    return entries


"""
Agents for: Monitoring & Control, Risk Response, Risk Plan

Each agent exposes a small set of tools backed by DocumentAnalysisService
and follows the same LangGraph workflow pattern used in EmotionAgent.
"""


### Shared tools -----------------------------------------------------------

@tool
async def summarize_documents() -> str:
    """Summarize all documents in the uploads folder using resume_text."""
    files = _list_upload_files()
    summaries = []
    for path in files:
        try:
            text = extract_text(path)
            if not text:
                # try OCR on images extracted from PDF
                imgs = extract_images(path, output_dir=os.path.join(os.path.dirname(path), "_extracted"))
                ocrs = ocrMethod(imgs)
                text = "\n".join([t for _, t in ocrs])
            # call resume_text which is async
            summ = await resume_text(text[:20000]) if text else ""
            summaries.append(f"== {os.path.basename(path)} ==\n{summ}")
        except Exception as e:
            summaries.append(f"Erro ao resumir {os.path.basename(path)}: {e}")
    return "\n\n".join(summaries) if summaries else "Nenhum documento encontrado."


@tool
async def semantic_search_documents(query: str) -> str:
    """Run a semantic search across the corpus (uses sentence-transformers)."""
    files = _list_upload_files()
    best = []
    for path in files:
        try:
            text = extract_text(path)
            if not text:
                continue
            score = semanticSearch(text, query)
            best.append((score, os.path.basename(path)))
        except Exception:
            continue
    best.sort(reverse=True)
    return "\n".join([f"{s:.4f} - {n}" for s, n in best[:10]]) if best else "Nenhum resultado encontrado."


@tool
async def extract_tables_from_docs() -> str:
    """Extract tables from all documents in the uploads folder."""
    files = _list_upload_files()
    results = []
    for path in files:
        try:
            tables = extract_tables(path)
            results.append(f"{os.path.basename(path)}: {len(tables)} tabelas")
        except Exception as e:
            results.append(f"{os.path.basename(path)}: erro {e}")
    return "\n".join(results) if results else "Nenhum documento encontrado."


shared_tools = [summarize_documents, semantic_search_documents, extract_tables_from_docs]


### Monitoring & Control Agent --------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


def _create_llm():
    return ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.3,
        api_key=GROQ_API_KEY
    )


def monitoring_callLlama(state: AgentState):
    messages = state['messages']
    model = _create_llm()
    llm_with_tools = model.bind_tools(shared_tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


async def monitoring_callTool(state: AgentState):
    messages = state['messages']
    last_messages = messages[-1]
    tool_outputs = []

    if hasattr(last_messages, 'tool_calls') and last_messages.tool_calls:
        for tool_call in last_messages.tool_calls:
            # handle both dict and object-shaped tool_call
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args') or {}
                tool_call_id = tool_call.get('id')
            else:
                tool_name = getattr(tool_call, 'name', None)
                tool_args = getattr(tool_call, 'args', {})
                tool_call_id = getattr(tool_call, 'id', None)

            if tool_name == 'summarize_documents':
                out = await summarize_documents.ainvoke()
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            elif tool_name == 'semantic_search_documents':
                q = tool_args.get('query') if isinstance(tool_args, dict) else None
                out = await semantic_search_documents.ainvoke(q or "")
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            elif tool_name == 'extract_tables_from_docs':
                out = await extract_tables_from_docs.ainvoke()
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            else:
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=f"Unknown tool: {tool_name}"))
        return {"messages": tool_outputs}
    return state


def monitoring_should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if getattr(last_message, 'tool_calls', None):
        return "continue_tool_call"
    return "end"


monitoring_workflow = StateGraph(AgentState)
monitoring_workflow.add_node("llm", monitoring_callLlama)
monitoring_workflow.add_node("tool_node", monitoring_callTool)
monitoring_workflow.set_entry_point("llm")
monitoring_workflow.add_conditional_edges(
    "llm",
    monitoring_should_continue,
    {"continue_tool_call": "tool_node", "end": END}
)
monitoring_workflow.add_edge("tool_node", "llm")
monitoring_app = monitoring_workflow.compile()


### Risk Response Agent ---------------------------------------------------

def response_callLlama(state: AgentState):
    messages = state['messages']
    model = _create_llm()
    llm_with_tools = model.bind_tools(shared_tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


async def response_callTool(state: AgentState):
    messages = state['messages']
    last_messages = messages[-1]
    tool_outputs = []

    if hasattr(last_messages, 'tool_calls') and last_messages.tool_calls:
        for tool_call in last_messages.tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args') or {}
                tool_call_id = tool_call.get('id')
            else:
                tool_name = getattr(tool_call, 'name', None)
                tool_args = getattr(tool_call, 'args', {})
                tool_call_id = getattr(tool_call, 'id', None)

            if tool_name == 'summarize_documents':
                out = await summarize_documents.ainvoke()
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            elif tool_name == 'semantic_search_documents':
                q = tool_args.get('query') if isinstance(tool_args, dict) else None
                out = await semantic_search_documents.ainvoke(q or "")
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            else:
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=f"Unknown tool: {tool_name}"))
        return {"messages": tool_outputs}
    return state


def response_should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if getattr(last_message, 'tool_calls', None):
        return "continue_tool_call"
    return "end"


response_workflow = StateGraph(AgentState)
response_workflow.add_node("llm", response_callLlama)
response_workflow.add_node("tool_node", response_callTool)
response_workflow.set_entry_point("llm")
response_workflow.add_conditional_edges(
    "llm",
    response_should_continue,
    {"continue_tool_call": "tool_node", "end": END}
)
response_workflow.add_edge("tool_node", "llm")
response_app = response_workflow.compile()


### Risk Plan Agent -------------------------------------------------------

def plan_callLlama(state: AgentState):
    messages = state['messages']
    model = _create_llm()
    llm_with_tools = model.bind_tools(shared_tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


async def plan_callTool(state: AgentState):
    messages = state['messages']
    last_messages = messages[-1]
    tool_outputs = []

    if hasattr(last_messages, 'tool_calls') and last_messages.tool_calls:
        for tool_call in last_messages.tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args') or {}
                tool_call_id = tool_call.get('id')
            else:
                tool_name = getattr(tool_call, 'name', None)
                tool_args = getattr(tool_call, 'args', {})
                tool_call_id = getattr(tool_call, 'id', None)

            if tool_name == 'summarize_documents':
                out = await summarize_documents.ainvoke()
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            elif tool_name == 'extract_tables_from_docs':
                out = await extract_tables_from_docs.ainvoke()
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(out)))
            else:
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=f"Unknown tool: {tool_name}"))
        return {"messages": tool_outputs}
    return state


def plan_should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if getattr(last_message, 'tool_calls', None):
        return "continue_tool_call"
    return "end"


plan_workflow = StateGraph(AgentState)
plan_workflow.add_node("llm", plan_callLlama)
plan_workflow.add_node("tool_node", plan_callTool)
plan_workflow.set_entry_point("llm")
plan_workflow.add_conditional_edges(
    "llm",
    plan_should_continue,
    {"continue_tool_call": "tool_node", "end": END}
)
plan_workflow.add_edge("tool_node", "llm")
plan_app = plan_workflow.compile()
