import os
import asyncio

from langchain.agents import initialize_agent, AgentType, Tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from src.agents.environment_organizational_agents_tools.EmotionAgent import app as emotion_agent_app

async def invoke_emotion_agent_as_tool_async(text_to_analyze: str) -> str:
    """
    Invokes the LangGraph emotion analysis agent with the provided text.
    This function acts as the bridge between the main agent and the tool agent.
    """
    print(f"\n### External Agent: Calling the Internal Agent of Emotion Analysis to: '{text_to_analyze}' ###")
    
    input_messages = [HumanMessage(content=text_to_analyze)]
    input_state = {"messages": input_messages}

    final_state = await emotion_agent_app.ainvoke(input_state)
    
    if final_state and 'messages' in final_state and final_state['messages']:
        last_message = final_state['messages'][-1]
        print(f"### Internal Agent of Emotion Final Answer: {last_message.content} ###")
        return last_message.content
    return "Error: The emotion analysis agent did not return a valid response."

def invoke_emotion_agent_as_tool(text_to_analyze: str) -> str:
    """
    Wrapper síncrono para o Tool do LangChain.
    """
    return asyncio.run(invoke_emotion_agent_as_tool_async(text_to_analyze))

emotion_agent_tool_wrapper = Tool(
    name="EmotionAnalysisAgent",
    func=invoke_emotion_agent_as_tool,
    description="Useful for analyzing the emotion and polarity of a text. It takes the text as input and returns the detected emotion and polarity."
)

GROQ_API_KEY = os.getenv("API_KEY")
llm_emotion_agent = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.7,
        api_key=GROQ_API_KEY
    )

outers_agent = initialize_agent(
    tools=[emotion_agent_tool_wrapper], 
    llm=llm_emotion_agent,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True, 
    handle_parsing_errors=True
)