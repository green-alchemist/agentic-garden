# clients/cli_agent/run.py
from src.agent import agent_app # <-- This is the corrected import path
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List

def main():
    """Runs the agent with a simple, non-streaming invoke call."""
    print("🤖 Coding Assistant w/ Memory is ready. Type 'exit' to quit.")
    
    messages: List[BaseMessage] = []
    
    while True:
        question = input("You: ")
        if question.lower() == 'exit':
            break
        
        messages.append(HumanMessage(content=question))
        
        # The agent's internal state now manages the message format
        inputs = {"messages": messages}
        
        response = agent_app.invoke(inputs)

        if "messages" in response:
            # Get the last message in the list, which is the AI's response
            ai_response = response["messages"][-1]
            if isinstance(ai_response, AIMessage):
                print(f"Assistant: {ai_response.content}")
                # The returned state is the new, complete history
                messages = response["messages"]
            else:
                 print("Assistant: I'm sorry, I encountered an error parsing the response.")
        else:
            print("Assistant: I'm sorry, I encountered an error.")

        print("-" * 20)

if __name__ == "__main__":
    main()