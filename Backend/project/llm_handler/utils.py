# utils.py

# In-memory chat memory (can be swapped with Redis, DB later)
chat_memory = {}  # Structure: {user_id: [{"role": ..., "content": ...}, ...]}


def truncate_history(history, max_len=10):
    return history[-max_len:]


def safe_import(module_path, attr="fetch"):
    try:
        module = __import__(module_path, fromlist=[attr])
        return getattr(module, attr)
    except Exception as e:
        return lambda _: {"error": f"Import failed: {str(e)}"}
