"""LLM Prompt templates"""
import platform
from operate.config import Config

config = Config()
USER_QUESTION = "What would you like me to do?"

SYSTEM_PROMPT_STANDARD = """You are REVA, an AI controlling a {os} computer.

Available actions:
1. click - {{"operation": "click", "x": 0.5, "y": 0.5, "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["super"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "done", "thought": "reason"}}

Return JSON array only.
Objective: {objective}
"""

SYSTEM_PROMPT_LABELED = """You are REVA, an AI controlling a {os} computer.
Screenshot has labeled UI elements with IDs (~1, ~2, etc).

Available actions:
1. click - {{"operation": "click", "label": "~1", "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["super"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "done", "thought": "reason"}}

Return JSON array only.
Objective: {objective}
"""

def get_system_prompt(model, objective):
    os_name = platform.system()
    if model in ["fast-gpt", "gpt-4-with-som"]:
        return SYSTEM_PROMPT_LABELED.format(os=os_name, objective=objective)
    return SYSTEM_PROMPT_STANDARD.format(os=os_name, objective=objective)

def get_user_prompt():
    return "Take the next action. Return JSON array only."

def get_user_first_message_prompt():
    return "Analyze screen and take first action. Return JSON array only."

def get_som_prompt(operation, df):
    return f"Select label to click for: {operation}"
