"""LLM Prompt templates"""
import platform

USER_QUESTION = "What would you like me to do?"

SYSTEM_PROMPT = """You are REVA, an AI controlling a {os} computer.

Available actions:
1. click - {{"operation": "click", "x": 0.5, "y": 0.5, "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["ctrl", "c"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "done", "thought": "reason"}}

Return JSON array only.

Objective: {objective}
"""

def get_system_prompt(model, objective):
    return SYSTEM_PROMPT.format(os=platform.system(), objective=objective)

def get_user_prompt():
    return "Take the next action. Return JSON array."

def get_user_first_message_prompt():
    return "Analyze screen and take first action. Return JSON array."
