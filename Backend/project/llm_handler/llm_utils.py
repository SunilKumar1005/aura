# llm_utils.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
MODEL = "gpt-4"

def call_llm(prompt, system_prompt=None, stream=False):
    messages = [{"role": "user", "content": prompt}]
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.6,
            stream=False
        )
        content = completion.choices[0].message.content
        # print(f"🔍 Raw LLM Response: {content}")
        return content
    except Exception as e:
        print(f"🔍 Error in call_llm: {str(e)}")
        return f"Error: {str(e)}"

def call_llm_with_history(prompt_text_with_conversation):
    messages = [{"role": "user", "content": prompt_text_with_conversation}]
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.6,
            stream=True
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        print(f"🔍 Error in call_llm_with_history: {str(e)}")
        yield ""
