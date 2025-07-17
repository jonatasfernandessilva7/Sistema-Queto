import operator
import requests

from typing import (
    Annotated,
    Sequence,
    TypedDict
)

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage
)
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

from src.backend.utils.ConnectionWithLlamaApiGroqUtils import llama_api_call

"""
defined tools with decorator tool
"""
@tool
def meetingTool():
    backend_url = "localhost://8080/v1"
    try:
        response = requests.get(f"{backend_url}{'parameter'}")
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error calling backend service: {e}"
    pass

tools = [meetingTool]

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
    model = llama_api_call
    llm_with_tools = model.bind_tools(tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def callTool():
    pass

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

"""Run"""
if __name__ == "__main__":
    print("AI Backend Service Agent (Type 'exit' to quit)")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Exiting conversation.")
            break

        initial_state = {"messages": [HumanMessage(content=user_input)]}

        for s in app.stream(initial_state):
            if "__end__" not in s:
                for key, value in s.items():
                    if key == "messages":
                        if isinstance(value, list) and value:
                            last_msg = value[-1]
                            if isinstance(last_msg, AIMessage):
                                print(f"Agent: {last_msg.content}")
                            elif isinstance(last_msg, ToolMessage):
                                print(f"Tool Output: {last_msg.content}")
            else:
                final_messages = s["__end__"]["messages"]
                if final_messages:
                    last_final_message = final_messages[-1]
                    if isinstance(last_final_message, AIMessage):
                        print(f"Agent: {last_final_message.content}")