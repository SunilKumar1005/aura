import os

def render_prompt(relative_path, context_dict):
    base_dir = os.path.dirname(__file__)  # path to llm_handler/
    full_path = os.path.join(base_dir, relative_path)

    with open(full_path, "r", encoding="utf-8") as f:
        template = f.read()

    for key, value in context_dict.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    return template
