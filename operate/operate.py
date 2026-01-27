"""Main agent loop"""
import sys
import os
import time
import asyncio
import platform
from loguru import logger
from operate.config import Config
from operate.exceptions import ModelNotRecognizedException
from operate.models.prompts import USER_QUESTION, get_system_prompt
from operate.utils.style import ANSI_GREEN, ANSI_RED, ANSI_BLUE, ANSI_RESET, ANSI_BRIGHT_MAGENTA
from operate.utils.operating_system import OperatingSystem
from operate.models.apis import get_next_action

config = Config()
operating_system = OperatingSystem()

def main(model, terminal_prompt=None, voice_mode=False, verbose_mode=False):
    """Main entry point"""
    config.verbose = verbose_mode

    if config.validation(model, voice_mode):
        print(f"{ANSI_RED}Error: API key not set{ANSI_RESET}")
        return

    print(f"{ANSI_GREEN}[REVA]{ANSI_RESET} Starting...")

    objective = terminal_prompt or input(f"{USER_QUESTION}\n> ")

    system_prompt = get_system_prompt(model, objective)
    messages = [{"role": "system", "content": system_prompt}]

    session_id = None

    for i in range(30):
        time.sleep(2)
        logger.info(f"Loop {i+1}")

        try:
            [operations, messages], session_id = asyncio.run(
                get_next_action(model, messages, objective, session_id)
            )

            if operate(operations, model):
                break

        except Exception as e:
            print(f"{ANSI_RED}Error: {e}{ANSI_RESET}")
            break

def operate(operations, model):
    """Execute operations"""
    for op in operations:
        time.sleep(1)
        op_type = op.get("operation", "").lower()
        thought = op.get("thought", "")

        print(f"{ANSI_BLUE}Action:{ANSI_RESET} {op_type}")
        if thought:
            print(f"  Thought: {thought}")

        if op_type == "press":
            operating_system.press(op.get("keys", []))
        elif op_type == "write":
            operating_system.write(op.get("content", ""))
        elif op_type == "click":
            operating_system.mouse({"x": op.get("x"), "y": op.get("y")})
        elif op_type == "scroll":
            operating_system.scroll()
        elif op_type == "done":
            print(f"{ANSI_GREEN}Done:{ANSI_RESET} {op.get('summary')}")
            return True
        else:
            print(f"{ANSI_RED}Unknown: {op_type}{ANSI_RESET}")
            return True

    return False
