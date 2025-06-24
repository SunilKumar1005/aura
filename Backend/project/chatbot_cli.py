import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv() 

api_key = os.getenv("OPENAI_API_KEY")
# print("OPENAI_API_KEY:", api_key)

client = OpenAI(api_key=api_key)

MODEL = "gpt-4"

chat_history = [
    {"role": "system", "content": "You are a helpful AI assistant for a diagnostic center client support team. Answer like a human customer service agent, be concise and clear."}
]

print(" AI Chatbot Ready. Type your message below (type 'exit' to quit)\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Exiting chat.")
        break

    chat_history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=MODEL,
        messages=chat_history,
        temperature=0.6,
        stream=True
    )

    full_response = ""
    # reply = response.choices[0].message.content
    for event in response:
        msg = event.choices[0].delta.content
        print(msg, end="", flush=True)
        if msg:
            full_response += msg

    chat_history.append({"role": "assistant", "content": full_response})
    # print(chat_history)
