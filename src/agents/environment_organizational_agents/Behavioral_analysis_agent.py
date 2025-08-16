import os
import operator

from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from src.backend.services.CaptureSystemLogs.CaptureSystemLogs import main as coletar_logs
from src.agents.environment_organizational_agents.EmotionAgent import analyzeEmotionFromText

GROQ_API_KEY = os.getenv("API_KEY")

"""
Tool: Capture and analyze behavior from logs
"""
@tool
async def analyzeBehavioralPatterns() -> str:
    """
    Captures system logs and analyzes activities and behaviors.
    Integrates with emotional analysis to generate behavioral insights.
    """
    # Coletar logs do sistema
    coletar_logs()
    if not os.path.exists("coleta_de_logs_sistema.log"):
        return "Nenhum log encontrado."

    with open("coleta_de_logs_sistema.log", "r") as f:
        logs = f.read()

    # Usar EmotionAgent para avaliar a "carga emocional" dos logs (textual)
    emotion_result = await analyzeEmotionFromText.ainvoke(logs[:2000])  

    analysis = f"""
    --- Behavioral Analysis Report ---
    Logs analyzed: {len(logs.splitlines())} lines
    Emotions detected: {emotion_result}

    Possible patterns:
    - Frequent logins/logouts = possible instability in use
    - Relevant applications open
    - Unusual activity times
    ---------------------------------
    """
    return analysis

tools = [analyzeBehavioralPatterns]

"""
define agent state
"""
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

"""
define the nodes
"""
def callLlama(state: AgentState):
    messages = state["messages"]
    model = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.6,
        api_key=GROQ_API_KEY
    )
    llm_with_tools = model.bind_tools(tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

async def callTool(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    tool_outputs = []

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call_dict in last_message.tool_calls:
            tool_name = tool_call_dict.get("name")
            tool_call_id = tool_call_dict.get("id")

            if tool_name == "analyzeBehavioralPatterns":
                output = await analyzeBehavioralPatterns.ainvoke()
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(output)))
            else:
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=f"Unknown tool: {tool_name}"))
        return {"messages": tool_outputs}
    return state

"""
Define Conditional Edge Logic
"""
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "continue_tool_call"
    else:
        return "end"

workflow = StateGraph(AgentState)
workflow.add_node("llm", callLlama)
workflow.add_node("tool_node", callTool)
workflow.set_entry_point("llm")

workflow.add_conditional_edges(
    "llm",
    should_continue,
    {
        "continue_tool_call": "tool_node",
        "end": END,
    }
)

workflow.add_edge("tool_node", "llm")

app = workflow.compile()
