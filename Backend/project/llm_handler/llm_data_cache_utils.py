import os
import json
from glob import glob

CACHE_DIR = "llm_data_cache"

def ensure_client_dir(client_fk):
    client_dir = os.path.join(CACHE_DIR, str(client_fk))
    os.makedirs(client_dir, exist_ok=True)
    return client_dir

def save_llm_data(client_fk, session_id, fn, data):
    client_dir = ensure_client_dir(client_fk)
    # List all files for this client
    files = sorted(glob(os.path.join(client_dir, "*.json")), key=os.path.getmtime)
    # If more than 2, delete the oldest
    if len(files) >= 3:
        os.remove(files[0])
    # Save new data
    file_path = os.path.join(client_dir, f"{session_id}_{fn}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path

def load_last_llm_data(client_fk, n=3):
    client_dir = ensure_client_dir(client_fk)
    files = sorted(glob(os.path.join(client_dir, "*.json")), key=os.path.getmtime, reverse=True)
    data_list = []
    for file in files[:n]:
        with open(file, "r", encoding="utf-8") as f:
            data_list.append(json.load(f))
    return data_list 