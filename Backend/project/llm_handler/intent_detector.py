import os
import json
from llm_handler.llm_utils import call_llm

def detect_intent(merged_history: str) -> dict:
    """
    Accepts a merged conversation string.
    Explicitly combines the instructions from the prompt template and the conversation before calling the LLM.
    """
    # Read the prompt template (instructions)
    base_dir = os.path.dirname(__file__)
    full_path = os.path.join(base_dir, "prompts/intent_detection_prompt.txt")
    with open(full_path, "r", encoding="utf-8") as f:
        instructions = f.read()

    # Combine instructions and conversation
    prompt = f"{instructions.strip()}\n\nConversation:\n{merged_history.strip()}"

    try:
        # print(f"🔍 Prompt: {prompt}")
        response = call_llm(prompt)
        result = json.loads(response)
        # print(f"🔍 Successfully parsed JSON: {result}")
        required_fields = ["intent", "functions_to_call", "prompt_to_use", "comment"]
        if not all(field in result for field in required_fields):
            raise ValueError("Missing required fields in LLM response")
        # print(f"🔍 Intent Detection Result: {result}")
        return result
    except Exception as e:
        print(f"🔍 Error in detect_intent: {str(e)}")
        return {
            "intent": "other_intent", 
            "prompt_to_use": "general_support_response_prompt.txt",
            "functions_to_call": [],
            "comment": "Error processing user request"
        }
