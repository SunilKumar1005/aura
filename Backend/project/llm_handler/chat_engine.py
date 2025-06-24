import json
from llm_handler.intent_detector import detect_intent
from llm_handler.prompt_builder import generate_response_prompt
from llm_handler.llm_utils import call_llm_with_history
from llm_handler.utils import chat_memory
from llm_handler.data_fetchers import llm_input_data_summary
from nocodb_handler import log_message, log_intent_result
from llm_handler.llm_data_cache_utils import save_llm_data, load_last_llm_data

def merge_history_for_intent(conversation_history, user_message):
    merged = ""
    if conversation_history and len(conversation_history) > 0:
        for turn in conversation_history:
            role = "User" if turn["role"] == "user" else "Bot"
            merged += f"{role}: {turn['content']}\n"
    merged += f"User: {user_message}\n"
    return merged


async def run_chat_pipeline(user_id, client_id, user_message, conversation_history=None, session_id=None):
    # 1. Merge history for intent detection
    merged_history = merge_history_for_intent(conversation_history, user_message)
    # print(f"🔍 Merged History: {merged_history}")
    intent_result = detect_intent(merged_history)
    
    intent = intent_result.get("intent", "other_intent")
    prompt_file = intent_result.get("prompt_to_use", "default_prompt.txt")
    functions_to_call = intent_result.get("functions_to_call", [])
    if isinstance(functions_to_call, str):
        functions_to_call = [functions_to_call]
    elif not isinstance(functions_to_call, list):
        functions_to_call = []

    print(f"🔍 Intent: {intent}")
    print(f"🔍 Prompt File: {prompt_file}")
    print(f"🔍 Functions to Call: {functions_to_call}")

    # 2. Log intent result to NoCoDB
    if session_id is not None:
        await log_intent_result(
            client_fk=str(client_id),
            session_id=session_id,
            message=intent_result.get("comment", ""),
            intent=intent,
            functions=functions_to_call,
            entities={},  # Add entity extraction if available
            status="Intent Detected",
            message_source="intent_bot",
            prompt=intent_result.get("prompt_to_use", "")
        )

    # 3. Fetch data based on detected function(s) and save to cache
    fetched_data = {}
    for fn in functions_to_call:
        try:
            func = getattr(llm_input_data_summary, fn)
            data = func(client_id)
            fetched_data[fn] = data
            # Save the data for this client/session/function
            print(f"🔍 Saving data for {fn} and session {session_id}")
            save_llm_data(client_id, session_id, fn, data)
        except Exception as e:
            fetched_data[fn] = {"error": str(e)}

    # Load last 3 data points for this client
    data_from_previous_llm_call = load_last_llm_data(client_id, n=3)

    # 4. Prepare prompt using data + template
    # print(f"🔍 Fetched Data: {fetched_data}")
    prompt_text_with_conversation = generate_response_prompt(
        merged_history,
        intent_result.get("prompt_to_use"),
        fetched_data,
        data_from_previous_llm_call=data_from_previous_llm_call
    )

    # Return the generator for streaming
    return call_llm_with_history(prompt_text_with_conversation)
