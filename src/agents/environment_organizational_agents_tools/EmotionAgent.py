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

from src.AiServices.services.AiEmotionAnalysisService import emotionAnalysis

GROQ_API_KEY = os.getenv("API_KEY")

"""
defined tools with decorator tool
"""
@tool
async def analyzeEmotionFromText(text: str) -> str:
    """
    :param text:
    :return:
    """
    result = emotionAnalysis(text)
    if "error" in result:
        return f"Error during emotion analysis: {result['error']}"
    return f"Emotion analysis {result['emotion']}, Polarity: {result['polarity']:.2f}"

tools = [analyzeEmotionFromText]

"""
define agent state
"""
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

"""
define the nodes
"""
def callLlama(state: AgentState):
    """
    Invokes the LLM model to generate a response or decide on tool usage.
    """
    messages = state['messages']
    model = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.7,
        api_key=GROQ_API_KEY
    )
    llm_with_tools = model.bind_tools(tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

async def callTool(state: AgentState):
    messages = state['messages']
    last_messages = messages[-1]
    tool_outputs = []

    if hasattr(last_messages, 'tool_calls') and last_messages.tool_calls:
        for tool_call_dict in last_messages.tool_calls:
            if not isinstance(tool_call_dict, dict):
                print(f"Unexpected tool_call type: {type(tool_call_dict)}. Expected dict or ToolCall.")
                tool_name = tool_call_dict.name
                tool_args = tool_call_dict.args
                tool_call_id = tool_call_dict.id
            else:
                tool_name = tool_call_dict.get("name")
                tool_args = tool_call_dict.get("args")
                tool_call_id = tool_call_dict.get("id")

            if tool_name == "analyzeEmotionFromText":
                text = tool_args.get("text")
                if text:
                    print(f"---calling tool analyze emotion---")
                    output = await analyzeEmotionFromText.ainvoke(text)
                    print("text\n")
                    tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=str(output)))
                    print("tools\n")
                else:
                    tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=f"Error: 'text' argument missing for {tool_name} tool."))
                    print("tool1")
            else:
                tool_outputs.append(ToolMessage(tool_call_id=tool_call_id, content=f"Unknown tool: {tool_name}"))
                print("tool2")
        print(tool_outputs,"\n")
        return {"messages": tool_outputs}
    return state


"""
Define Conditional Edge Logic
"""
def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "continue_tool_call"
    else:
        return "end"

"""
Build the LangGraph Workflow
"""
workflow = StateGraph(AgentState)
workflow.add_node("llm", callLlama)
workflow.add_node("tool_node", callTool)
workflow.set_entry_point("llm")

workflow.add_conditional_edges(
    "llm",
    should_continue,
    {
        "continue_tool_call": "tool_node",
        "end": END
    }
)

workflow.add_edge("tool_node", "llm")

app = workflow.compile()