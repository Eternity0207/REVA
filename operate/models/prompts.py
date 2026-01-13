"""LLM Prompt templates"""
import platform
from operate.config import Config

config = Config()
USER_QUESTION = "What would you like me to do?"

VALID_OPERATIONS = {"click", "write", "press", "scroll", "done"}

SYSTEM_PROMPT_STANDARD = """You are REVA, an AI controlling a {os} computer.
Analyze the screenshot and execute actions to complete the objective.

CRITICAL: Respond with ONLY a JSON array. No explanations.

Available actions:
1. click - {{"operation": "click", "x": 0.5, "y": 0.5, "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["super"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "what was done", "thought": "reason"}}

x, y are screen percentages (0.0 to 1.0).
Keys: "super" for Win key, "ctrl", "alt", "shift", "enter", "tab"

Example: [{{"operation": "press", "keys": ["super"], "thought": "Opening menu"}}]

Objective: {objective}
"""

SYSTEM_PROMPT_LABELED = """You are REVA, an AI controlling a {os} computer.
Screenshot has labeled UI elements (~1, ~2, etc).

CRITICAL: Respond with ONLY a JSON array. No explanations.

Available actions:
1. click - {{"operation": "click", "label": "~1", "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["super"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "what was done", "thought": "reason"}}

Example: [{{"operation": "click", "label": "~3", "thought": "Clicking search"}}]

Objective: {objective}
"""

def get_system_prompt(model, objective):
    os_name = platform.system()
    if model in ["fast-gpt", "gpt-4-with-som", "fast-gemini"]:
        return SYSTEM_PROMPT_LABELED.format(os=os_name, objective=objective)
    return SYSTEM_PROMPT_STANDARD.format(os=os_name, objective=objective)

def get_user_prompt():
    return "Take the next action. JSON array only."

def get_user_first_message_prompt():
    return "First action. JSON array only."

def get_som_prompt(operation, df):
    return f"Select label for: {operation}"

def validate_operation(op):
    return op.get("operation", "").lower() in VALID_OPERATIONS
