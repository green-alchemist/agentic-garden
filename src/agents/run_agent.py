# run_agent.py
from src.agents.coding_assistant import agent_app
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
        
        simple_messages = [{"role": msg.type, "content": msg.content} for msg in messages]
        
        inputs = {
            "messages": simple_messages,
            "temperature": 0.1
        }
        # print(f"\n[CLIENT] Calling agent with inputs: {inputs}")
        
        response = agent_app.invoke(inputs)
        
        # print(f"[CLIENT] Received response from agent: {response}")

        if generation := response.get("generation"):
            print(f"Assistant: {generation}")
            messages.append(AIMessage(content=generation))
        else:
            print("Assistant: I'm sorry, I encountered an error.")

        print("-" * 20)

if __name__ == "__main__":
    main()