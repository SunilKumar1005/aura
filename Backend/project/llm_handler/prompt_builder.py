import json
from llm_handler.prompts_loader import render_prompt

def generate_response_prompt(merged_history, prompt_file, fetched_data, data_from_previous_llm_call=None):
    # Read the system prompt and the main prompt instructions from files
    system_prompt_path = "prompts/SYSTEM_PROMPT.txt"
    prompt_path = f"prompts/{prompt_file}"
    system_prompt = render_prompt(system_prompt_path, {})
    prompt_instructions = render_prompt(prompt_path, {})
    
    # Build the full prompt: system prompt, instructions, conversation, and data
    prompt_text = f"{system_prompt.strip()}\n\n{prompt_instructions.strip()}\n\nConversation:\n{merged_history.strip()}\n\nData:\n{json.dumps(fetched_data, indent=2)}"
    if data_from_previous_llm_call:
        prompt_text += f"\n\nData from previous LLM calls:\n{json.dumps(data_from_previous_llm_call, indent=2)}"
    return prompt_text
